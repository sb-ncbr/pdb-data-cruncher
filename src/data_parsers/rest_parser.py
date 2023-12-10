from typing import Any, Optional
import logging

from src.models import LigandInfo, ProteinDataFromRest
from src.exception import RestParsingError


def parse_rest(pdb_id: str,
               protein_summary_json: dict[str, Any],
               protein_assembly_json: dict[str, Any],
               protein_molecules_json: dict[str, Any],
               ligand_infos: dict[str, LigandInfo]) -> bool:
    logging.debug("[%s] Start parsing rest.", pdb_id)
    try:
        parse_rest_unsafe(pdb_id,
                          protein_summary_json,
                          protein_assembly_json,
                          protein_molecules_json,
                          ligand_infos)
        logging.debug("[%s] Rest parsed successfully", pdb_id)
        return True
    except RestParsingError as ex:
        logging.error("[%s] %s", pdb_id, ex)
        return False
    except Exception as ex:
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return False


# TODO after done, consider being less punishing for some errors (maybe eg. one wrong file with different id doesn't
# mean all are useless, and reconsider the way data extraction and dealing with errors works
# TODO consider returning loading files into here, esp. after the thing is divided into multiple functions
# it may be more officient to avoid holding the information and just load it straight before processing it
def parse_rest_unsafe(pdb_id: str,
                      protein_summary_json: dict[str, Any],
                      protein_assembly_json: dict[str, Any],
                      protein_molecules_json: dict[str, Any],
                      ligand_infos: dict[str, LigandInfo]) -> ProteinDataFromRest:
    protein_data = ProteinDataFromRest(pdb_id=pdb_id)
    noncritical_issues = []

    preferred_assembly_id = parse_protein_summary(pdb_id, protein_summary_json, protein_data)

    # start of processing protein_assembly_json

    if pdb_id not in protein_summary_json.keys():
        raise RestParsingError("Given assembly json doesn't have currently processed pdb_id.")

    biopolymer_entity_count: dict[int, int] = {}
    ligand_entity_count: dict[int, int] = {}
    water_entity_count: dict[int, int] = {}

    preferred_assembly_full = find_preferred_assembly_by_id(
        pdb_id, preferred_assembly_id, protein_assembly_json
    )
    if preferred_assembly_full is None:
        raise RestParsingError(f"Preferred assembly with assembly id {preferred_assembly_id} "
                               f"was not found in assembly json.")

    protein_data.molecular_weight = preferred_assembly_full.get("molecular_weight")

    for entity_json in preferred_assembly_full.get("entities", []):
        try:
            entity_id = int(entity_json["entity_id"])
            molecule_type = entity_json["molecule_type"].lower()  # lower for case-insensitive comparisons
            number_of_copies = int(entity_json["number_of_copies"])
        except KeyError:
            noncritical_issues.append("Entity in assembly json is missing entity_id, molecule_type or number_of_copies."
                                      "Entity skipped.")
            continue
        except ValueError:
            noncritical_issues.append("Entity in assembly json has non-int value as entity_id or number_of_copies."
                                      "Entity skipped.")
            continue

        molecule_type = molecule_type.lower()  # change to lowercase for case insensitive comparison
        if molecule_type in ["carbohydrate polymer",
                             "polypeptide(l)",
                             "polypeptide(d)",
                             "polyribonucleotide",
                             "polydeoxyribonucleotide",
                             "polysaccharide(d)",
                             "polysaccharide(l)",
                             "polydeoxyribonucleotide/polyribonucleotide hybrid",
                             "cyclic-pseudo-peptide",
                             "peptide nucleic acid"]:
            biopolymer_entity_count[entity_id] = number_of_copies
        elif molecule_type == "bound":
            ligand_entity_count[entity_id] = number_of_copies
        elif molecule_type == "water":
            water_entity_count[entity_id] = number_of_copies
        elif molecule_type == "other":
            pass  # ignore "other" type
        else:
            noncritical_issues.append(f"Entity {entity_id} in assembly json has unknown type '{molecule_type}'. "
                                      f"Entity skipped.")

    total_ligand_count = sum(ligand_entity_count.values())
    protein_data.assembly_biopolymer_count = sum(biopolymer_entity_count.values())
    protein_data.assembly_ligand_count = total_ligand_count
    protein_data.assembly_water_count = sum(water_entity_count.values())
    protein_data.assembly_unique_biopolymer_count = len(biopolymer_entity_count)
    protein_data.assembly_unique_ligand_count = len(ligand_entity_count)

    # end of processing assembly

    # start of processing molecules json
    if pdb_id not in protein_molecules_json.keys():
        raise RestParsingError("Given molecules json doesn't have currently processed pdb_id.")

    total_biopolymer_weight: float = 0.0
    total_ligand_weight: float = 0.0
    total_water_weight: float = 0.0
    ligand_flexibility_raw: float = 0.0
    ligand_flexibility_error: bool = False

    for molecule_json in protein_molecules_json.get(pdb_id):
        try:
            molecule_id = int(molecule_json.get("entity_id"))
        except TypeError:  # thrown if int(...) gets None or otherwise not a valid number in string
            noncritical_issues.append("Molecule in molecule json is missing entity_id or it isn't a valid number. "
                                      "Skipping processing of this molecule.")
            continue

        try:
            molecule_weight = float(molecule_json.get("weight"))
        except TypeError:  # thrown if molecule_json has no weight or if it isn't convertible to float
            noncritical_issues.append("Molecule in molecule json is missing weight or it isn't convertible to float. "
                                      "Skipping processing of this molecule.")
            continue

        if molecule_id in biopolymer_entity_count.keys():  # molecule is biopolymer
            total_biopolymer_weight += molecule_weight * biopolymer_entity_count.get(molecule_id)
        if molecule_id in ligand_entity_count.keys():  # molecule is ligand
            total_ligand_weight += molecule_weight * ligand_entity_count.get(molecule_id)
            suitable_chem_comp_ids = [chemp_comp_id
                                      for chemp_comp_id in molecule_json.get("chem_comp_ids", [])
                                      if chemp_comp_id in ligand_infos.keys()]
            if len(suitable_chem_comp_ids) == 0:
                ligand_flexibility_error = True  # TODO this may not be the desirable behaviour, changed it a bit
                continue

            ligand_info = ligand_infos.get(suitable_chem_comp_ids[0])
            ligand_flexibility_raw += ligand_info.flexibility * ligand_entity_count.get(molecule_id)
        if molecule_id in water_entity_count.keys():  # molecule is water
            total_water_weight += molecule_weight * water_entity_count.get(molecule_id)

    protein_data.assembly_biopolymer_weight = total_biopolymer_weight
    protein_data.assembly_ligand_weight = total_ligand_weight
    protein_data.assembly_water_weight = total_water_weight
    if total_ligand_count > 0 and not ligand_flexibility_error:
        protein_data.assembly_ligand_flexibility = ligand_flexibility_raw / total_ligand_count

    # TODO tweak this
    # TODO refactor funciton properly
    # TODO introduce unified diagnostics
    # TODO process returned data and make a dataclass for them instead of dict
    print(protein_data)
    return protein_data


def parse_protein_summary(pdb_id: str, protein_summary_json: Any, protein_data: ProteinDataFromRest) -> str:
    # check pdbId is the same as expected and structure has just one pdbId key with expected value
    if len(protein_summary_json.keys()) > 1:
        raise RestParsingError("Protein summary has more than one pdbId key.")
    if len(protein_summary_json.get("pdb_id", [])) > 1:
        raise RestParsingError("Protein summary array has more than one object.")
    if pdb_id not in protein_summary_json.keys():
        raise RestParsingError(f"Conflicting pdbIds, expected '{pdb_id}', got keys '{protein_summary_json.keys()} "
                               f"inside summary file.")
    protein_summary_list = protein_summary_json[pdb_id][0]
    # extract basic protein information
    release_date_string = protein_summary_list.get("release_date")
    protein_data.release_date = (release_date_string[:4]
                                              if release_date_string is not None
                                              else None)
    rest_methods = protein_summary_list.get("experimental_method_class")
    protein_data.rest_method = rest_methods[0] if len(rest_methods) > 1 else None
    protein_data.submission_site = protein_summary_list.get("deposition_site")
    protein_data.processing_site = protein_summary_list.get("processing_site")

    # collect preferred assembly
    preferred_assembly_summary = None
    for assembly in protein_summary_list.get("assemblies", []):
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


def find_preferred_assembly_by_id(pdb_id: str,
                                  assembly_id: str,
                                  protein_assembly_json: dict[str, Any]) -> Optional[dict[str, Any]]:
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
