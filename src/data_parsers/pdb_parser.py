import logging
import math
import os

from Bio.PDB import MMCIFParser
from Bio.PDB.Atom import Atom
from Bio.PDB.Residue import Residue

from src.models.protein_data_from_pdb import ProteinDataFromPDB
from src.config import Config


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


def parse_pdb(pdb_id: str, config: Config):
    logging.debug("[%s] PDB parsing started", pdb_id)
    filepath = os.path.join(config.path_to_pdb_files, f"{pdb_id}.cif")
    _parse_pdb_unsafe(pdb_id, filepath)


def _parse_pdb_unsafe(pdb_id: str, filepath: str):
    protein_data = ProteinDataFromPDB(pdb_id=pdb_id)
    parser = MMCIFParser()
    structure = parser.get_structure(pdb_id, filepath)

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
        if not residue_is_water(residue):
            protein_data.ligand_count_no_water += 1
            protein_data.hetatm_count_no_water += hetatm_count_in_residue
        if atom_list_contains_metal(hetatm_list):
            protein_data.ligand_count_metal += 1
            protein_data.hetatm_count_metal += hetatm_count_in_residue

    # calculate more metrics from these atom counts
    protein_data.all_atom_count = protein_data.atom_count_without_hetatms + protein_data.hetatm_count

    if protein_data.all_atom_count > 0:
        protein_data.all_atom_count_ln = math.log(protein_data.all_atom_count)
    if protein_data.ligand_count > 0:
        protein_data.ligand_ratio = protein_data.hetatm_count / protein_data.ligand_count
    if protein_data.ligand_count_no_water > 0:
        protein_data.ligand_ratio_no_water = protein_data.hetatm_count_no_water / protein_data.ligand_count_no_water

    protein_data.hetatm_count_no_metal = protein_data.hetatm_count - protein_data.hetatm_count_metal
    protein_data.ligand_count_no_metal = protein_data.ligand_count - protein_data.ligand_count_metal
    protein_data.hetatm_count_no_water_no_metal = protein_data.hetatm_count_no_water - protein_data.hetatm_count_metal
    protein_data.ligand_count_no_water_no_metal = protein_data.ligand_count_no_water - protein_data.ligand_count_metal

    if protein_data.ligand_count_metal > 0:
        protein_data.ligand_ratio_metal = protein_data.hetatm_count_metal / protein_data.ligand_count_metal
    if protein_data.ligand_count_no_metal > 0:
        protein_data.ligand_ratio_no_metal = protein_data.hetatm_count_no_metal / protein_data.ligand_count_no_metal
    if protein_data.ligand_count_no_water_no_metal > 0:
        protein_data.ligand_ratio_no_water_no_metal = (
                protein_data.hetatm_count_no_water_no_metal / protein_data.ligand_count_no_water_no_metal
        )
    # END OF PART TO REFACTOR 1

    pass
    # continue on line 257


def residue_is_water(residue: Residue) -> bool:
    return residue.resname == "HOH"


def atom_list_contains_metal(atom_list: list[Atom]) -> bool:
    for atom in atom_list:
        if atom.element.lower() in METAL_ELEMENT_NAMES:
            return True
    return False
