import logging
import math
import os
from typing import Optional

from Bio.PDB.MMCIF2Dict import MMCIF2Dict

from src.config import Config
from src.models.protein_data_from_pdbx import ProteinDataFromPDBx
from src.models.diagnostics import Diagnostics, IssueType
from src.exception import PDBxParsingError


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


def parse_pdbx(pdb_id: str, config: Config) -> Optional[ProteinDataFromPDBx]:
    logging.debug("[%s] PDB parsing started", pdb_id)
    filepath = os.path.join(config.path_to_pdb_files, f"{pdb_id}.cif")
    logging.debug("[%s] Will extract cif file from: %s", pdb_id, filepath)
    try:
        protein_data = _parse_pdbx_unsafe(pdb_id, filepath)
        return protein_data
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # We want to catch broad exception here so unforseen data error doesn't kill the whole data processing.
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return None


def _parse_pdbx_unsafe(pdb_id: str, filepath: str) -> ProteinDataFromPDBx:
    protein_data = ProteinDataFromPDBx(pdb_id=pdb_id)
    diagnostics = Diagnostics()
    mmcif_dict = MMCIF2Dict(filepath)

    pdb_id_from_mmcif = get_first_item(mmcif_dict, "_entry.id").lower()
    if pdb_id_from_mmcif != pdb_id:
        raise PDBxParsingError(f"PDB ID aquired from the given mmcif file itself does not match expected value."
                               f"Expected {pdb_id}, extracted {pdb_id_from_mmcif} instead.")

    # PART 1 FOR REFACTOR
    atom_site_relevant_info = zip(
        mmcif_dict["_atom_site.group_PDB"],  # ATOM or HETATM
        mmcif_dict["_atom_site.type_symbol"],  # element symbol
        mmcif_dict["_atom_site.label_comp_id"],  # residue name label
        mmcif_dict["_atom_site.auth_seq_id"],  # residue ids (by author)
        mmcif_dict["_atom_site.auth_comp_id"],  # residue names (by author)
        mmcif_dict["_atom_site.auth_asym_id"],  # residue chain ids (by author)
    )
    encountered_ligands = {}  # collects element of ligands for futher processing

    for atom_type, symbol, residue_name_label, residue_id, residue_name, residue_chain in atom_site_relevant_info:
        if atom_type == "ATOM":
            protein_data.atom_count_without_hetatms += 1
        if atom_type == "HETATM":
            ligand_identifier = (residue_id, residue_name, residue_chain)
            if ligand_identifier in encountered_ligands:
                encountered_ligands[ligand_identifier].append((symbol, residue_name_label))
            else:
                encountered_ligands[ligand_identifier] = [(symbol, residue_name_label)]

    for ligand_contents_list in encountered_ligands.values():
        has_water = False
        has_metal = False
        for symbol, residue_name_label in ligand_contents_list:
            if residue_name_label == "HOH":
                has_water = True
            if symbol.lower() in METAL_ELEMENT_NAMES:
                has_metal = True

        hetatms_in_this_ligand = len(ligand_contents_list)
        protein_data.ligand_count += 1
        protein_data.hetatm_count += hetatms_in_this_ligand
        if not has_water:
            protein_data.ligand_count_no_water += 1
            protein_data.hetatm_count_no_water += hetatms_in_this_ligand
        if has_metal:
            protein_data.ligand_count_metal += 1
            protein_data.hetatm_count_metal += hetatms_in_this_ligand
    # PART 1 FOR REFACTOR END

    calculate_additional_counts_and_ratios(protein_data)
    extract_straightforward_data(mmcif_dict, protein_data)

    # WEIGHT PART - another refactoring candidate
    entity_ids = mmcif_dict.get("_entity.id")
    entity_types = mmcif_dict.get("_entity.type")
    molecule_counts = mmcif_dict.get("_entity.pdbx_number_of_molecules")
    formula_weights = mmcif_dict.get("_entity.formula_weight")

    for entity_id, entity_type, molecule_count_str, formula_weight_str in zip(
            entity_ids, entity_types, molecule_counts, formula_weights):
        try:
            molecule_count = int(molecule_count_str)
        except (TypeError, ValueError) as ex:
            diagnostics.add_issue(IssueType.DATA_ITEM_ERROR,
                                  f"Entity with id {entity_id} has invalid item _entity.pdbx_number_of_molecules. "
                                  f"This entity is ignored for the purpose of counting weights. Reason: {ex}")
            continue
        try:
            raw_weight = float(formula_weight_str)
        except (TypeError, ValueError) as ex:
            diagnostics.add_issue(IssueType.DATA_ITEM_ERROR,
                                  f"Entity with id {entity_id} has invalid item _entity.formula_weight. "
                                  f"This entity is ignored for the purpose of counting weights. Reason: {ex}")
            continue

        if entity_type == "polymer":
            protein_data.polymer_weight += raw_weight * molecule_count
        elif entity_type == "non-polymer":
            protein_data.nonpolymer_weight_no_water += raw_weight * molecule_count
        elif entity_type == "water":
            protein_data.water_weight += raw_weight * molecule_count
        else:
            diagnostics.add_issue(IssueType.DATA_ITEM_ERROR,
                                  f"Entity with id {entity_id} has unexpected entity type {entity_type}. "
                                  f"Its weight is not processed.")

    protein_data.polymer_weight /= 1000  # Da -> kDa adjustment
    # TODO is this alright? :point_up:
    protein_data.nonpolymer_weight = protein_data.nonpolymer_weight_no_water + protein_data.water_weight
    protein_data.structure_weight = protein_data.polymer_weight + (protein_data.nonpolymer_weight / 1000)

    return protein_data


def extract_straightforward_data(mmcif_dict: MMCIF2Dict, data: ProteinDataFromPDBx) -> None:
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
    data.struct_keywords_pdbx = get_first_item(mmcif_dict, "_struct_keywords.pdbx_keywords")
    data.experimental_method = get_first_item(mmcif_dict, "_exptl.method")

    # get first item as number (there is always just one item and it's a number)
    data.em_3d_reconstruction_resolution = get_first_float(mmcif_dict, "_em_3d_reconstruction.resolution")
    data.refinement_resolution_high = get_first_float(mmcif_dict, "_refine.ls_d_res_high")
    data.reflections_resolution_high = get_first_float(mmcif_dict, "_reflns.d_resolution_high")
    data.diffraction_ambient_temperature = get_first_int(mmcif_dict, "_diffrn.ambient_temp")
    data.crystal_grow_temperature = get_first_float(mmcif_dict, "_exptl_crystal_grow.temp")
    data.crystal_grow_ph = get_first_float(mmcif_dict, "_exptl_crystal_grow.pH")

    # get those that need other kind of small change
    data.aa_count = len(mmcif_dict.get("_entity_poly_seq.entity_id", []))
    struct_keywords_text = get_first_item(mmcif_dict, "_struct_keywords.text")
    crystal_growth_methods = get_first_item(mmcif_dict, "_exptl_crystal_grow.method")
    if struct_keywords_text:
        data.struct_keywords_text = [value.strip() for value in struct_keywords_text.split(",")]
    if crystal_growth_methods:
        data.crystal_grow_methods = [value.strip() for value in crystal_growth_methods.split(",")]


def calculate_additional_counts_and_ratios(data: ProteinDataFromPDBx) -> None:
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


def get_first_float(mmcif_dict: MMCIF2Dict, key: str) -> Optional[float]:
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
        return float(get_first_item(mmcif_dict, key))
    except (TypeError, ValueError):
        return None


def get_first_int(mmcif_dict: MMCIF2Dict, key: str) -> Optional[int]:
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
        return int(get_first_item(mmcif_dict, key))
    except (TypeError, ValueError):
        return None


def get_first_item(mmcif_dict: MMCIF2Dict, key: str) -> Optional[str]:
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
            raise PDBxParsingError(f"DEVELOPER'S ERROR IN LOGIC: Only one relevant item in mmcif item {key} expected. "
                                   f"Got {value_list}. Fix the logic in the pdbx_parser, type in protein data "
                                   f"and wherever it is used.")
        return value_list[0]
    return None
