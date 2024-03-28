import logging
import math
from dataclasses import dataclass, field
from typing import Optional, Generator

from Bio.PDB.MMCIF2Dict import MMCIF2Dict

from src.models.protein_data import ProteinDataFromPDBx
from src.models import Diagnostics
from src.exception import PDBxParsingError
from src.utils import to_float, to_int
from src.constants import METAL_ELEMENT_NAMES


@dataclass(slots=True)
class AtomSiteItem:
    """
    Holding relevant information from _atom_site for further processing.
    """

    atom_id: str
    is_hetatm: bool
    element_symbol: str
    residue_name_label: str
    residue_name_auth: str
    residue_id_auth: str
    residue_chain_id: str
    model_number: str
    occupancy: float


@dataclass(slots=True)
class LigandIdentifier:
    """
    Unique combination of atom_site values to identify ligand for the purposes of PDBx parsing.
    """

    residue_id_auth: str
    residue_name_auth: str
    residue_chain_id: str

    def __hash__(self):
        """
        Redefine hash for the purposes of using the instance as dictionary key.
        :return: Hash of the dataclass instance.
        """
        return hash((self.residue_id_auth, self.residue_name_auth, self.residue_chain_id))


@dataclass(slots=True)
class EncounteredLigand:
    """
    Ligand found during PDBx parsing, collects information about its atoms that is then processed.
    """

    id: LigandIdentifier
    atoms: list[AtomSiteItem] = field(default_factory=list)


def parse_pdbx(pdb_id: str, filepath: str) -> Optional[ProteinDataFromPDBx]:
    """
    Extracts and calculates protein information from mmcif (PDBx) file.
    :param pdb_id: PDB ID to extract.
    :param filepath: Path to the mmcif file.
    :return: Collected protein data.
    """
    logging.debug("[%s] PDBx parsing started. Will extract mmcif file from: %s", pdb_id, filepath)
    try:
        protein_data, diagnostics = _parse_pdbx_unsafe(pdb_id, filepath)
        diagnostics.process_into_logging("PDBx parsing", pdb_id)
        return protein_data
    except PDBxParsingError as ex:
        logging.error("[%s] %s", pdb_id, ex)
        return None
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # We want to catch broad exception here so unforseen data error doesn't kill the whole data processing.
        logging.exception("[%s] PDBx parsing: Encountered unexpected issue: %s", pdb_id, ex)
        return None


def _parse_pdbx_unsafe(pdb_id: str, filepath: str) -> tuple[ProteinDataFromPDBx, Diagnostics]:
    """
    Extracts and calculates protein information from mmcif (PDBx) file. Unsafe - can raise exceptions.
    :param pdb_id: PDB ID to extract.
    :param filepath: Path to the mmcif file.
    :return: Collected protein data and diagnostics about non-critical data issues.
    :raises PDBxParsingError: In case of critical issue that prevents further data extraction.
    """
    protein_data = ProteinDataFromPDBx(pdb_id=pdb_id)
    diagnostics = Diagnostics()
    mmcif_dict = MMCIF2Dict(filepath)

    _check_pdb_id_from_mmcif(mmcif_dict, pdb_id)
    _extract_atom_and_ligand_counts(mmcif_dict, protein_data)
    _extract_straightforward_data(mmcif_dict, protein_data)
    _extract_data_resolution(mmcif_dict, protein_data)
    _extract_weight_data(mmcif_dict, protein_data, diagnostics)
    _calculate_additional_counts_and_ratios(protein_data)

    return protein_data, diagnostics


def _check_pdb_id_from_mmcif(mmcif_dict: MMCIF2Dict, expected_pdb_id: str) -> None:
    """
    Checks whether the PDB ID inside mmcif file matches the expected PDB ID the program is currently processing.
    :param mmcif_dict: Holds information from mmcif file.
    :param expected_pdb_id: Expected pdb id value (lowercase).
    :raises PDBxParsingError: If PDB ID inside mmcif is different from the expected one or missing.
    """
    pdb_id_from_mmcif = _get_first_item(mmcif_dict, "_entry.id")
    if not pdb_id_from_mmcif or pdb_id_from_mmcif.lower() != expected_pdb_id:
        raise PDBxParsingError(
            f"PDB ID aquired from the given mmcif file itself does not match expected value."
            f"Expected {expected_pdb_id}, extracted '{pdb_id_from_mmcif}' instead."
        )


def _extract_atom_and_ligand_counts(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> None:
    """
    Extracts and stores protein data about atom/hetatm counts and ligand counts.
    :param mmcif_dict: Holds data extracted from mmcif file.
    :param data: Protein data instance in which the collected information is stored.
    """
    encountered_ligands = _extract_atom_counts(mmcif_dict, data)
    _calculate_ligand_counts(encountered_ligands, data)


def _extract_atom_counts(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> list[EncounteredLigand]:
    """
    Extract atom (and hetatm) counts from mmcif and collect information about unique ligands encountered.
    :param mmcif_dict: Holds data extracted from mmcif file.
    :param data: Protein data instance in which the collected information is stored.
    :return: List of unique encountered ligands with atoms they have inside.
    """
    encountered_ligands = {}
    # in the case of multiple structure models in _atom_site, count with only the first one
    try:
        only_relevant_model_number = mmcif_dict["_atom_site.pdbx_PDB_model_num"][0]
    except (IndexError, KeyError) as ex:
        raise PDBxParsingError("Required item _atom_site.pdbx_PDB_model_num not found in mmcif file or empty.") from ex

    unrelevant_model_number_present = False
    processed_unsure_atoms = {}

    for atom_item in _atomsite_item_generator(mmcif_dict):
        if atom_item.model_number != only_relevant_model_number:
            unrelevant_model_number_present = True
            continue

        if atom_item.occupancy != 1.0:  # atom could be present twice with different positions
            if atom_item.atom_id in processed_unsure_atoms:  # atom with this id was already processed
                processed_unsure_atoms[atom_item.atom_id].append(atom_item.occupancy)
                continue

            processed_unsure_atoms[atom_item.atom_id] = [atom_item.occupancy]

        if atom_item.is_hetatm:  # is HETATM
            ligand_identifier = LigandIdentifier(
                residue_id_auth=atom_item.residue_id_auth,
                residue_name_auth=atom_item.residue_name_auth,
                residue_chain_id=atom_item.residue_chain_id,
            )
            if ligand_identifier in encountered_ligands:
                encountered_ligands[ligand_identifier].atoms.append(atom_item)
            else:
                encountered_ligands[ligand_identifier] = EncounteredLigand(id=ligand_identifier, atoms=[atom_item])
        else:  # is ATOM
            data.atom_count_without_hetatms += 1

    if unrelevant_model_number_present:
        logging.info(
            "[%s] Multiple model numbers present in mmcif file atom site. Only those with model number %s "
            "were counted.",
            data.pdb_id,
            only_relevant_model_number,
        )

    _log_incomplete_atom_occupancies(data.pdb_id, processed_unsure_atoms)

    return list(encountered_ligands.values())


def _calculate_ligand_counts(encountered_ligands: list[EncounteredLigand], data: ProteinDataFromPDBx) -> None:
    """
    Go through the extracted ligands and get relevant counts from them.
    :param encountered_ligands: List of unique encountered ligands with atoms they have inside.
    :param data: Protein data instance in which the collected information is stored.
    """
    # goes through the collected ligand (hetatm) groups
    for encountered_ligand in encountered_ligands:
        has_water = False
        has_metal = False
        for atom_item in encountered_ligand.atoms:
            if atom_item.residue_name_label == "HOH":
                has_water = True
            if atom_item.element_symbol.lower() in METAL_ELEMENT_NAMES:
                has_metal = True

        hetatms_in_this_ligand = len(encountered_ligand.atoms)
        data.ligand_count += 1
        data.hetatm_count += hetatms_in_this_ligand
        if not has_water:
            data.ligand_count_no_water += 1
            data.hetatm_count_no_water += hetatms_in_this_ligand
        if has_metal:
            data.ligand_count_metal += 1
            data.hetatm_count_metal += hetatms_in_this_ligand


def _atomsite_item_generator(mmcif_dict: MMCIF2Dict) -> Generator[AtomSiteItem, None, None]:
    """
    Takes relevant information from _atom_site in mmcif and generates items from it for further processing.
    :param mmcif_dict: Holds loaded mmcif data.
    :return: Generated AtomSiteItem, or None.
    """
    try:
        atom_id_iter = iter(mmcif_dict["_atom_site.id"])
        atom_type_iter = iter(mmcif_dict["_atom_site.group_PDB"])  # ATOM or HETATM
        symbol_type_iter = iter(mmcif_dict["_atom_site.type_symbol"])  # element symbol
        residue_name_label_iter = iter(mmcif_dict["_atom_site.label_comp_id"])  # residue name label
        residue_id_auth_iter = iter(mmcif_dict["_atom_site.auth_seq_id"])  # residue ids (by author)
        residue_name_auth_iter = iter(mmcif_dict["_atom_site.auth_comp_id"])  # residue names (by author)
        residue_chain_id_iter = iter(mmcif_dict["_atom_site.auth_asym_id"])  # residue chain ids (by author)
        model_num_iter = iter(mmcif_dict["_atom_site.pdbx_PDB_model_num"])  # model numbers
        occupancy_iter = iter(mmcif_dict["_atom_site.occupancy"])
    except KeyError as ex:
        raise PDBxParsingError("Required _atom_site item not found in mmcif, cannot proceed with parsing.") from ex

    while True:
        try:
            yield AtomSiteItem(
                atom_id=next(atom_id_iter),
                is_hetatm=(next(atom_type_iter) == "HETATM"),
                element_symbol=next(symbol_type_iter),
                residue_name_label=next(residue_name_label_iter),
                residue_name_auth=next(residue_name_auth_iter),
                residue_id_auth=next(residue_id_auth_iter),
                residue_chain_id=next(residue_chain_id_iter),
                model_number=next(model_num_iter),
                occupancy=to_float(next(occupancy_iter)),
            )
        except StopIteration:  # raised when the first list runs out of items
            return


def _extract_weight_data(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx, diagnostics: Diagnostics):
    """
    Extracts protein data from mmcif_dict related to weights.
    :param mmcif_dict: Holds loaded mmcif data.
    :param data: Stores extracted protein data.
    :param diagnostics: Stores information about important data missing.
    """
    for entity_id, entity_type, molecule_count_str, formula_weight_str in zip(
        mmcif_dict.get("_entity.id"),
        mmcif_dict.get("_entity.type"),
        mmcif_dict.get("_entity.pdbx_number_of_molecules"),
        mmcif_dict.get("_entity.formula_weight"),
    ):
        molecule_count = to_int(molecule_count_str)
        raw_weight = to_float(formula_weight_str)
        if molecule_count is None:
            diagnostics.add(
                f"Entity with id {entity_id} has invalid item _entity.pdbx_number_of_molecules "
                f"('{molecule_count_str}'). For further processing, it is assumed that the count was 1."
            )
            molecule_count = 1
        if raw_weight is None:
            diagnostics.add(
                f"Entity with id {entity_id} has invalid item _entity.formula_weight ('{formula_weight_str}'). "
                f"This entity is ignored for the purpose of counting weights."
            )
            continue

        if entity_type == "polymer":
            data.polymer_weight_kda += (raw_weight * molecule_count) / 1000  # Da -> kDa adjustment
        elif entity_type == "non-polymer":
            data.nonpolymer_weight_no_water_da += raw_weight * molecule_count
        elif entity_type == "water":
            data.water_weight_da += raw_weight * molecule_count
        else:
            diagnostics.add(
                f"Entity with id {entity_id} has unexpected entity type {entity_type}. " f"Its weight is not processed."
            )

    data.nonpolymer_weight_da = data.nonpolymer_weight_no_water_da + data.water_weight_da
    data.structure_weight_kda = data.polymer_weight_kda + (data.nonpolymer_weight_da / 1000)


def _extract_straightforward_data(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> None:
    """
    Extracts protein data from given mmcif_dict, that are either saved as is or require just small adjustments
    without any calculations or significant transformation.
    :param mmcif_dict: Mmcif dict holding information from mmcif file.
    :param data: Class that will be filled with extracted informaiton.
    """
    experimental_method = _get_first_item(mmcif_dict, "_exptl.method")
    if experimental_method is not None:
        data.experimental_method = experimental_method.upper()
    data.aa_count = len(mmcif_dict.get("_entity_poly_seq.entity_id", []))


def _extract_data_resolution(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> None:
    """
    Extracts and determines structure resolution from the three possible locations.
    :param mmcif_dict: Contains data from the mmcif file.
    :param data: Collected data about this protein.
    """
    em_3d_reconstruction_resolution = to_float(_get_first_item(mmcif_dict, "_em_3d_reconstruction.resolution"))
    refinement_resolution_high = to_float(_get_first_item(mmcif_dict, "_refine.ls_d_res_high"))
    reflections_resolution_high = to_float(_get_first_item(mmcif_dict, "_reflns.d_resolution_high"))

    if refinement_resolution_high is not None:
        data.resolution = refinement_resolution_high
    elif reflections_resolution_high is not None:
        data.resolution = reflections_resolution_high
    elif em_3d_reconstruction_resolution is not None:
        data.resolution = em_3d_reconstruction_resolution


def _calculate_additional_counts_and_ratios(data: ProteinDataFromPDBx) -> None:
    """
    Calculates addional protein data that can be calculated from already collected protein data.
    It includes all_atom_count(_ln), ligand_ratio, ligand_ratio_no_water, and hetatm counts, ligand counts
    and ligand ratios for metal, no_metal and no_water_no_metal.
    :param data: Protein data collected so far.
    """
    data.all_atom_count = data.atom_count_without_hetatms + data.hetatm_count

    if data.all_atom_count > 0:
        data.all_atom_count_ln = math.log(data.all_atom_count)
    if data.ligand_count > 0:
        data.ligand_ratio = data.hetatm_count / data.ligand_count
    if data.ligand_count_no_water > 0:
        data.ligand_ratio_no_water = data.hetatm_count_no_water / data.ligand_count_no_water

    data.hetatm_count_no_metal = data.hetatm_count - data.hetatm_count_metal
    data.ligand_count_no_metal = data.ligand_count - data.ligand_count_metal
    data.hetatm_count_no_water_no_metal = data.hetatm_count_no_water - data.hetatm_count_metal
    data.ligand_count_no_water_no_metal = data.ligand_count_no_water - data.ligand_count_metal

    if data.ligand_count_metal > 0:
        data.ligand_ratio_metal = data.hetatm_count_metal / data.ligand_count_metal
    if data.ligand_count_no_metal > 0:
        data.ligand_ratio_no_metal = data.hetatm_count_no_metal / data.ligand_count_no_metal
    if data.ligand_count_no_water_no_metal > 0:
        data.ligand_ratio_no_water_no_metal = data.hetatm_count_no_water_no_metal / data.ligand_count_no_water_no_metal

    data.aa_ligand_count = data.ligand_count + data.aa_count
    data.aa_ligand_count_no_water = data.ligand_count_no_water + data.aa_count


def _log_incomplete_atom_occupancies(pdb_id: str, processed_unsure_atoms: dict[str, list[float]]) -> None:
    """
    Goes through given atoms with less than 1.0 occupancies, and checks, and logs all that do not have other
    instances that would complete their occupancy to 1.0.
    :param pdb_id: Protein Id.
    :param processed_unsure_atoms: Dictionary with atom_id key and list of occupancy values.
    """
    incomplete_atom_count = 0
    for instance_occupancies in processed_unsure_atoms.values():
        if sum(instance_occupancies) != 1.0:
            incomplete_atom_count += 1
    if incomplete_atom_count > 0:
        logging.info(
            "[%s] %s atoms have sum of their occupancy less than 1.0 across their possible occurrences.",
            pdb_id,
            incomplete_atom_count,
        )


def _get_first_item(mmcif_dict: MMCIF2Dict, key: str) -> Optional[str]:
    """
    By default, MMCIF2DICT returns all values under given key as a list, even if there is only one of them.
    This function extracts such list, and returns only the first item from it.
    :param mmcif_dict: Mmcif dict from pdbx file.
    :param key: Key of item to extract.
    :return: First item from the list from mmcif dict under given key; or None if such does not exist.
    :raises PDBxParsingError: When multiple items are found in list under given key.
    """
    value_list = mmcif_dict.get(key)
    if value_list and len(value_list) > 0:
        if len(value_list) != 1:
            logging.warning(
                "Only one relevant item in mmcif item %s expected. Got %s. Other values have been ignored.",
                key,
                value_list,
            )
        return value_list[0]
    return None
