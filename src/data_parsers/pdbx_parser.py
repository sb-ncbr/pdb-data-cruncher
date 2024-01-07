import logging
import math
import os
from typing import TYPE_CHECKING, Optional

from Bio.PDB import MMCIFParser, is_aa
from Bio.PDB.MMCIF2Dict import MMCIF2Dict

from src.config import Config
from src.models.protein_data_from_pdbx import ProteinDataFromPDBx

if TYPE_CHECKING:
    from Bio.PDB.Atom import Atom
    from Bio.PDB.Residue import Residue


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
        # TODO only temporary alternative
        protein_data = _parse_pdbx_unsafe_alternative(pdb_id, filepath)
        return protein_data
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # We want to catch broad exception here so unforseen data error doesn't kill the whole data processing.
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return None


def _parse_pdbx_unsafe(pdb_id: str, filepath: str) -> ProteinDataFromPDBx:
    protein_data = ProteinDataFromPDBx(pdb_id=pdb_id)
    parser = MMCIFParser()
    structure = parser.get_structure(pdb_id, filepath)
    # TODO check what errors parsing can throw, and if any of them is not breaking
    # TODO parsing purely mmcif2dict would probably be faster (no need to build the structure)
    # consider the difference and if it would be worth it for decreased readability
    # This way of doing it is more transparent of what is happening.

    # PART TO REFACTOR 1
    residue_hetatm_groups = {}

    # go through all atoms, count simple atoms, store hetatms for future
    for atom in structure.get_atoms():
        residue = atom.parent
        # The first item in residue's id is "hetero flag". If it is present, it is heteroatom.
        if residue.get_id()[0] != " ":
            if residue in residue_hetatm_groups.keys():
                residue_hetatm_groups[residue].append(atom)
            else:
                residue_hetatm_groups[residue] = [atom]
        else:
            protein_data.atom_count_without_hetatms += 1

    # process hetatm grouped by residue_id
    for residue, hetatm_list in residue_hetatm_groups.items():
        hetatm_count_in_residue = len(hetatm_list)
        protein_data.ligand_count += 1
        protein_data.hetatm_count += hetatm_count_in_residue
        if not _is_water(residue):
            protein_data.ligand_count_no_water += 1
            protein_data.hetatm_count_no_water += hetatm_count_in_residue
        if _atom_list_contains_metal(hetatm_list):
            protein_data.ligand_count_metal += 1
            protein_data.hetatm_count_metal += hetatm_count_in_residue

    # calculate more metrics from these atom counts
    calculate_additional_protein_data(protein_data)
    # END OF PART TO REFACTOR 1

    alt_count = 0
    # count amino acids
    for residue in structure.get_residues():
        if is_aa(residue):
            protein_data.aa_count += 1
            alt_count += len(residue.child_list)
    # TODO does not count as expected in all the cases

    # TODO weights

    # under construction
    return protein_data


def _parse_pdbx_unsafe_alternative(pdb_id: str, filepath: str) -> ProteinDataFromPDBx:
    protein_data = ProteinDataFromPDBx(pdb_id=pdb_id)
    mmcif_dict = MMCIF2Dict(filepath)

    # parse keywords
    protein_data.structure_keywords = [value.strip() for value in mmcif_dict["_struct_keywords.text"][0].split(",")]

    # PART 1 FOR REFACTOR
    # TODO this part is potentially too resource greedy
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

    calculate_additional_protein_data(protein_data)

    protein_data.aa_count = len(mmcif_dict["_entity_poly_seq.entity_id"])

    # TODO weights

    return protein_data


def calculate_additional_protein_data(data: ProteinDataFromPDBx) -> None:
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


def _is_water(residue: 'Residue') -> bool:
    return residue.resname == "HOH"


def _atom_list_contains_metal(atom_list: list['Atom']) -> bool:
    for atom in atom_list:
        if atom.element.lower() in METAL_ELEMENT_NAMES:
            return True
    return False
