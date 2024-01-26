import logging
import math
from typing import Optional

from Bio.PDB.MMCIF2Dict import MMCIF2Dict

from src.models import ProteinDataFromPDBx, Diagnostics
from src.exception import PDBxParsingError
from src.utils import to_float


# turning off black formatter to keep the elements more readable
# fmt: off
METAL_ELEMENT_NAMES = {
        "li", "na", "k", "rb", "cs", "fr",
        "be", "mg", "ca", "sr", "ba", "ra",
        "lu", "la", "ce", "pr", "nd", "pm", "sm", "eu", "gd", "tb", "dy", "ho", "er", "tm", "yb",
        "lr", "ac", "th", "pa", "u", "np", "pu", "am", "cm", "bk", "cf", "es", "fm", "md", "no",
        "sc", "ti", "v", "cr", "mn", "fe", "co", "ni", "cu", "zn",
        "y", "zr", "nb", "mo", "tc", "ru", "rh", "pd", "ag", "cd",
        "hf", "ta", "w", "re", "os", "ir", "pt", "au", "hg",
        "rf", "db", "sg", "bh", "hs", "cn",
        "al", "ga", "in", "sn", "tl", "pb", "bi", "po", "fl"
}
# fmt: on


# pylint: disable=duplicate-code  # the code duplicate evaluation did not make sense in this case
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
    _extract_atom_counts(mmcif_dict, protein_data)
    _calculate_additional_counts_and_ratios(protein_data)
    _extract_straightforward_data(mmcif_dict, protein_data)
    _extract_weight_data(mmcif_dict, protein_data, diagnostics)

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


def _extract_atom_counts(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> None:
    """
    Extracts and stores protein data about atom/hetatm counts and ligand counts.
    :param mmcif_dict: Holds data extracted from mmcif file.
    :param data: Protein data instance in which the collected information is stored.
    """
    encountered_ligands = {}  # collects element of ligands for futher processing
    alt_hetatm_count_metal = 0
    for atom_type, symbol, residue_name_label, residue_id, residue_name, residue_chain in zip(
        mmcif_dict["_atom_site.group_PDB"],  # ATOM or HETATM
        mmcif_dict["_atom_site.type_symbol"],  # element symbol
        mmcif_dict["_atom_site.label_comp_id"],  # residue name label
        mmcif_dict["_atom_site.auth_seq_id"],  # residue ids (by author)
        mmcif_dict["_atom_site.auth_comp_id"],  # residue names (by author)
        mmcif_dict["_atom_site.auth_asym_id"],  # residue chain ids (by author)
    ):
        if atom_type == "ATOM":
            data.atom_count_without_hetatms += 1
        if atom_type == "HETATM":
            if symbol.lower() in METAL_ELEMENT_NAMES:
                alt_hetatm_count_metal += 1
            ligand_identifier = (residue_id, residue_name, residue_chain)
            if ligand_identifier in encountered_ligands:
                encountered_ligands[ligand_identifier].append((symbol, residue_name_label))
            else:
                encountered_ligands[ligand_identifier] = [(symbol, residue_name_label)]

    # goes through the collected ligand (hetatm) groups
    for ligand_contents_list in encountered_ligands.values():
        has_water = False
        has_metal = False
        for symbol, residue_name_label in ligand_contents_list:
            if residue_name_label == "HOH":
                has_water = True
            if symbol.lower() in METAL_ELEMENT_NAMES:
                has_metal = True

        hetatms_in_this_ligand = len(ligand_contents_list)
        data.ligand_count += 1
        data.hetatm_count += hetatms_in_this_ligand
        if not has_water:
            data.ligand_count_no_water += 1
            data.hetatm_count_no_water += hetatms_in_this_ligand
        if has_metal:
            data.ligand_count_metal += 1
            data.hetatm_count_metal += hetatms_in_this_ligand


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
        try:
            molecule_count = int(molecule_count_str)
        except (TypeError, ValueError) as ex:
            diagnostics.add(
                f"Entity with id {entity_id} has invalid item _entity.pdbx_number_of_molecules. "
                f"This entity is ignored for the purpose of counting weights. Reason: {ex}"
            )
            continue
        try:
            raw_weight = float(formula_weight_str)
        except (TypeError, ValueError) as ex:
            diagnostics.add(
                f"Entity with id {entity_id} has invalid item _entity.formula_weight. "
                f"This entity is ignored for the purpose of counting weights. Reason: {ex}"
            )
            continue

        if entity_type == "polymer":
            data.polymer_weight += raw_weight * molecule_count
        elif entity_type == "non-polymer":
            data.nonpolymer_weight_no_water += raw_weight * molecule_count
        elif entity_type == "water":
            data.water_weight += raw_weight * molecule_count
        else:
            diagnostics.add(
                f"Entity with id {entity_id} has unexpected entity type {entity_type}. " f"Its weight is not processed."
            )
    data.polymer_weight /= 1000  # Da -> kDa adjustment
    # TODO is this alright? :point_up:
    data.nonpolymer_weight = data.nonpolymer_weight_no_water + data.water_weight
    data.structure_weight = data.polymer_weight + (data.nonpolymer_weight / 1000)


def _extract_straightforward_data(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> None:
    """
    Extracts protein data from given mmcif_dict, that are either saved as is or require just small adjustments
    without any calculations or significant transformation.
    :param mmcif_dict: Mmcif dict holding information from mmcif file.
    :param data: Class that will be filled with extracted informaiton.
    """
    # get full lists of strings
    data.citation_journal_abbreviation = mmcif_dict.get("_citation.journal_abbrev")
    data.software_name = mmcif_dict.get("_software.name")
    data.gene_source_scientific_name = mmcif_dict.get("_entity_src_gen.pdbx_gene_src_scientific_name")
    data.host_organism_scientific_name = mmcif_dict.get("_entity_src_gen.pdbx_host_org_scientific_name")

    # get first item as string (there is always just one item)
    data.struct_keywords_pdbx = _get_first_item(mmcif_dict, "_struct_keywords.pdbx_keywords")
    data.experimental_method = _get_first_item(mmcif_dict, "_exptl.method")

    # get first item as number (there is always just one item and it's a number)
    data.em_3d_reconstruction_resolution = _get_first_float(mmcif_dict, "_em_3d_reconstruction.resolution")
    data.refinement_resolution_high = _get_first_float(mmcif_dict, "_refine.ls_d_res_high")
    data.reflections_resolution_high = _get_first_float(mmcif_dict, "_reflns.d_resolution_high")
    data.crystal_grow_temperatures = _get_first_float(mmcif_dict, "_exptl_crystal_grow.temp")
    data.crystal_grow_ph = _get_first_float(mmcif_dict, "_exptl_crystal_grow.pH")

    # get those that need other kind of small change
    data.aa_count = len(mmcif_dict.get("_entity_poly_seq.entity_id", []))
    struct_keywords_text = _get_first_item(mmcif_dict, "_struct_keywords.text")
    if struct_keywords_text:
        data.struct_keywords_text = [value.strip() for value in struct_keywords_text.split(",")]
    crystal_growth_methods = _get_first_item(mmcif_dict, "_exptl_crystal_grow.method")
    if crystal_growth_methods:
        data.crystal_grow_methods = [value.strip() for value in crystal_growth_methods.split(",")]
    ambient_temperatures = mmcif_dict.get("_diffrn.ambient_temp")
    if ambient_temperatures:
        data.diffraction_ambient_temperature = [to_float(value) for value in ambient_temperatures if to_float(value)]


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


def _get_first_float(mmcif_dict: MMCIF2Dict, key: str) -> Optional[float]:
    """
    By default, MMCIF2DICT returns all values under given key as a list, even if there is only one of them.
    This function extracts such list, and returns only the first item from it (converted to float).
    :param mmcif_dict: Mmcif dict from pdbx file.
    :param key: Key of item to extract.
    :return: First item from the list from mmcif dict under given key; or None if such does not exist of if the
    extracted value cannot be converted into valid float.
    :raises PDBxParsingError: When multiple items are found in list under given key.
    """
    try:
        return float(_get_first_item(mmcif_dict, key))
    except (TypeError, ValueError):
        return None


def _get_first_int(mmcif_dict: MMCIF2Dict, key: str) -> Optional[int]:
    """
    By default, MMCIF2DICT returns all values under given key as a list, even if there is only one of them.
    This function extracts such list, and returns only the first item from it (converted to int).
    :param mmcif_dict: Mmcif dict from pdbx file.
    :param key: Key of item to extract.
    :return: First item from the list from mmcif dict under given key; or None if such does not exist of if the
    extracted value cannot be converted into valid int.
    :raises PDBxParsingError: When multiple items are found in list under given key.
    """
    try:
        return int(_get_first_item(mmcif_dict, key))
    except (TypeError, ValueError):
        return None


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
            # TODO clause to double check the logic - can be deleted once the whole thing is run
            raise PDBxParsingError(
                f"DEVELOPER'S ERROR IN LOGIC: Only one relevant item in mmcif item {key} expected. Got {value_list}. "
                f"Fix the logic in the pdbx_parser, type in protein data and wherever it is used."
            )
        return value_list[0]
    return None
