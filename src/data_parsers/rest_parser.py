import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from src.config import BIOPOLYMER_MOLECULE_TYPES
from src.exception import RestParsingError
from src.models import LigandInfo, ProteinDataFromRest, Diagnostics, IssueType


@dataclass(slots=True)
class EntityCounts:
    """
    Internal class only. Entity holding biopolymers, ligands and waters count for better readability.
    """

    biopolymers: dict[int, int] = field(default_factory=dict)
    ligands: dict[int, int] = field(default_factory=dict)
    waters: dict[int, int] = field(default_factory=dict)


def parse_rest(
    pdb_id: str,
    protein_summary_json: dict[str, Any],
    protein_assembly_json: dict[str, Any],
    protein_molecules_json: dict[str, Any],
    ligand_infos: dict[str, LigandInfo],
) -> Optional[ProteinDataFromRest]:
    """
    Extracts and calculates protein information from given jsons.
    :param pdb_id: Id of protein.
    :param protein_summary_json: Full content of summary json.
    :param protein_assembly_json: Full content of assembly json.
    :param protein_molecules_json: Full content of molecules json.
    :param ligand_infos: Information about all ligands.
    :return: ProteinDataFromRest on success, None on critical failure.
    """
    logging.debug("[%s] Rest parsing started", pdb_id)
    try:
        protein_data, diagnostics = _parse_rest_unsafe(
            pdb_id,
            protein_summary_json,
            protein_assembly_json,
            protein_molecules_json,
            ligand_infos,
        )
        diagnostics.process_into_logging("REST parser", pdb_id)
        if protein_data.values_missing > 0:
            logging.info("[%s] %s values failed to be extracted. %s", pdb_id, protein_data.values_missing, protein_data)
        return protein_data
    except RestParsingError as ex:
        logging.error("[%s] %s", pdb_id, ex)
        return None
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # We want to catch broad exception here so unforseen data error doesn't kill the whole data processing.
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return None


# pylint: disable=too-many-arguments, too-many-locals
def _parse_rest_unsafe(
    pdb_id: str,
    protein_summary_json: dict[str, Any],
    protein_assembly_json: dict[str, Any],
    protein_molecules_json: dict[str, Any],
    ligand_infos: dict[str, LigandInfo],
) -> (ProteinDataFromRest, Diagnostics):
    """
    Extracts and calculates protein information from given jsons. Unsafe - can raise exceptions.
    :param pdb_id: Id of protein.
    :param protein_summary_json: Full content of summary json.
    :param protein_assembly_json: Full content of assembly json.
    :param protein_molecules_json: Full content of molecules json.
    :param ligand_infos: Information about all ligands.
    :return: Collected protein data and diagnostics from non-critical issues with data.
    :raises RestParsingError: When encountering critical issue that prevents data extraction completely.
    """
    # set up data structures
    protein_data = ProteinDataFromRest(pdb_id=pdb_id)  # holds parsed protein data
    diagnostics = Diagnostics()  # holds recoverable parsing mistakes

    # parse summary file
    if pdb_id not in protein_summary_json.keys():
        raise RestParsingError("Given assembly json doesn't have currently processed pdb_id.")
    preferred_assembly_id = _parse_protein_summary(pdb_id, protein_summary_json, protein_data)

    # find preferred assembly
    preferred_assembly_full = _find_preferred_assembly_by_id(pdb_id, preferred_assembly_id, protein_assembly_json)
    if preferred_assembly_full is None:
        raise RestParsingError(
            f"Preferred assembly with assembly id {preferred_assembly_id} was not found in assembly json."
        )

    # parse preferred assembly
    entity_counts = _parse_preferred_assembly(preferred_assembly_full, protein_data, diagnostics)

    # parse molecules
    _parse_molecules(pdb_id, protein_molecules_json, ligand_infos, entity_counts, protein_data, diagnostics)

    return protein_data, diagnostics


def _parse_molecules(
    pdb_id: str,
    protein_molecules_json: Any,
    ligand_infos: dict[str, LigandInfo],
    entity_counts: EntityCounts,
    protein_data: ProteinDataFromRest,
    diagnostics: Diagnostics,
) -> None:
    """
    Parses protein's molecule json into required information.
    :param pdb_id: Id of the protein.
    :param protein_molecules_json: Full content of molecule json.
    :param ligand_infos: Information about all ligands.
    :param entity_counts: Information about entity counts (biopolymers, water and ligands).
    :param protein_data: Dataclass for extracted information.
    :param diagnostics: Dataclass for non-critical issues with data.
    """
    # check if the data is even in the json
    if pdb_id not in protein_molecules_json.keys():
        raise RestParsingError("Given molecules json doesn't have currently processed pdb_id.")

    # setup data structures
    total_biopolymer_weight: float = 0.0
    total_ligand_weight: float = 0.0
    total_water_weight: float = 0.0
    ligand_flexibility_raw: float = 0.0
    total_ligand_count_with_flexibility: int = 0

    # parse molecules one by one
    for single_molecule_json in protein_molecules_json.get(pdb_id):
        try:
            molecule_id = int(single_molecule_json.get("entity_id"))
            molecule_weight = float(single_molecule_json.get("weight"))
        except (TypeError, ValueError):  # raised if conversion gets None or otherwise not a valid number in string
            diagnostics.add_issue(
                IssueType.DATA_ITEM_ERROR,
                "Ignored a molecule in molecule json. Its id or weight is missing or it isn't a valid number.",
            )
            continue

        if molecule_id in entity_counts.biopolymers.keys():  # molecule is biopolymer
            total_biopolymer_weight += molecule_weight * entity_counts.biopolymers.get(molecule_id)
        if molecule_id in entity_counts.ligands.keys():  # molecule is ligand
            total_ligand_weight += molecule_weight * entity_counts.ligands.get(molecule_id)
            suitable_chem_comp_ids = [
                chemp_comp_id
                for chemp_comp_id in single_molecule_json.get("chem_comp_ids", [])
                if chemp_comp_id in ligand_infos.keys()
            ]
            if len(suitable_chem_comp_ids) == 0:
                diagnostics.add_issue(
                    IssueType.DATA_ITEM_ERROR,
                    f"Ligand {molecule_id} in molecule json does not have any valid chem_com_id. "
                    f"This ligand will be ignored for the purpose of calculating ligand flexibility.",
                )
            elif len(suitable_chem_comp_ids) > 1:
                diagnostics.add_issue(
                    IssueType.DATA_ITEM_ERROR,
                    f"Ligand {molecule_id} in molecule json has more than one chem_comp_ids: {suitable_chem_comp_ids}. "
                    f"Only the first is taken into account.",
                )
            else:
                # if valid chem comp id was found, ligand flexibility can be counter (if not, it isn't counted into
                # total flexibility calculation)
                ligand_info = ligand_infos.get(suitable_chem_comp_ids[0])
                total_ligand_count_with_flexibility += 1
                ligand_flexibility_raw += ligand_info.flexibility * entity_counts.ligands.get(molecule_id)
        if molecule_id in entity_counts.waters.keys():  # molecule is water
            total_water_weight += molecule_weight * entity_counts.waters.get(molecule_id)

    # save results into protein_data
    protein_data.assembly_biopolymer_weight = total_biopolymer_weight / 1000.0
    protein_data.assembly_ligand_weight = total_ligand_weight
    protein_data.assembly_water_weight = total_water_weight
    if total_ligand_count_with_flexibility > 0:
        protein_data.assembly_ligand_flexibility = ligand_flexibility_raw / total_ligand_count_with_flexibility


def _parse_protein_summary(pdb_id: str, protein_summary_json: Any, protein_data: ProteinDataFromRest) -> str:
    """
    Parses protein's summary json, saving parsed information, and returns found preferred assembly id.
    :param pdb_id: Id of protein.
    :param protein_summary_json: Json will full contents of summary json.
    :param protein_data: Dataclass collecting parsed protein information.
    :return: Preferred assembly id.
    """
    # check pdbId is the same as expected and structure has just one pdbId key with expected value
    if len(protein_summary_json.keys()) > 1:
        raise RestParsingError("Protein summary has more than one pdbId key.")
    if len(protein_summary_json.get("pdb_id", [])) > 1:
        raise RestParsingError("Protein summary array has more than one object.")
    if pdb_id not in protein_summary_json.keys():
        raise RestParsingError(
            f"Conflicting pdbIds, expected '{pdb_id}', got keys '{protein_summary_json.keys()} inside summary file."
        )
    protein_summary_info = protein_summary_json[pdb_id][0]

    # extract basic protein information
    release_date_string = protein_summary_info.get("release_date")
    protein_data.release_date = release_date_string[:4] if release_date_string else None
    experimental_method_classes = protein_summary_info.get("experimental_method_class")
    protein_data.experimental_method_class = (
        experimental_method_classes[0] if len(experimental_method_classes) >= 1 else None
    )
    protein_data.submission_site = protein_summary_info.get("deposition_site")
    protein_data.processing_site = protein_summary_info.get("processing_site")

    # collect preferred assembly
    preferred_assembly_summary = None
    for assembly in protein_summary_info.get("assemblies", []):
        if assembly.get("preferred", False):
            preferred_assembly_summary = assembly
            break
    if preferred_assembly_summary is None:
        raise RestParsingError("No preffered assembly found.")

    # find the preferred assembly inside assembly json
    preferred_assembly_id = preferred_assembly_summary.get("assembly_id")
    if preferred_assembly_id is None:
        raise RestParsingError("No assembly_id found for preferred assembly in protein summary.")
    return preferred_assembly_id


def _find_preferred_assembly_by_id(pdb_id: str, assembly_id: str, protein_assembly_json: Any) -> Optional[Any]:
    """
    Find one assembly with given id inside the whole protein assembly json.
    :param pdb_id: Id of protein.
    :param assembly_id: Id of assembly to find.
    :param protein_assembly_json: Json dictionary with assembly information.
    :return: Dictionary of selected assembly, or None if none was found.
    """
    all_assemblies = protein_assembly_json.get(pdb_id, [])
    for assembly in all_assemblies:
        if assembly.get("assembly_id") == assembly_id:
            return assembly
    return None


def _parse_preferred_assembly(
    assembly_json: Any, protein_data: ProteinDataFromRest, diagnostics: Diagnostics
) -> EntityCounts:
    """
    Parses given preferred assembly, stores data in protein_data and returns entity counts for further parsing needs.
    :param assembly_json: Loaded json with the preferred assembly data.
    :param protein_data: Structure that holds extracted data
    :param diagnostics: Structure that holds any noncritical issues.
    :return: Entity counts (biopolymers, ligands and waters).
    """
    biopolymer_entity_count: dict[int, int] = {}
    ligand_entity_count: dict[int, int] = {}
    water_entity_count: dict[int, int] = {}

    protein_data.molecular_weight = assembly_json.get("molecular_weight")

    # go through each entity in assembly, decide what type it is and note it down in entity counts
    for entity_json in assembly_json.get("entities", []):
        try:
            entity_id = int(entity_json["entity_id"])
            molecule_type = entity_json["molecule_type"].lower()  # lower for case-insensitive comparisons
            number_of_copies = int(entity_json["number_of_copies"])
        except (KeyError, ValueError):
            diagnostics.add_issue(
                IssueType.DATA_ITEM_ERROR,
                "Ignored an entity in assembly json. Missing or invalid type of entity-id, molecule_type or "
                "number_of_copies.",
            )
            continue

        if molecule_type in [type_name.lower() for type_name in BIOPOLYMER_MOLECULE_TYPES]:
            biopolymer_entity_count[entity_id] = number_of_copies
        elif molecule_type == "bound":
            ligand_entity_count[entity_id] = number_of_copies
        elif molecule_type == "water":
            water_entity_count[entity_id] = number_of_copies
        elif molecule_type == "other":
            pass  # ignore "other" type
        else:
            diagnostics.add_issue(
                IssueType.DATA_ITEM_ERROR,
                f"Ignored entity {entity_id} in assembly json. Unknown molecule type '{molecule_type}'.",
            )

    total_ligand_count = sum(ligand_entity_count.values())
    protein_data.assembly_biopolymer_count = sum(biopolymer_entity_count.values())
    protein_data.assembly_ligand_count = total_ligand_count
    protein_data.assembly_water_count = sum(water_entity_count.values())
    protein_data.assembly_unique_biopolymer_count = len(biopolymer_entity_count)
    protein_data.assembly_unique_ligand_count = len(ligand_entity_count)

    return EntityCounts(biopolymers=biopolymer_entity_count, ligands=ligand_entity_count, waters=water_entity_count)
