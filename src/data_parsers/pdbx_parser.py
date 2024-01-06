import logging
import math
import os
from typing import TYPE_CHECKING, Optional

from Bio.PDB import MMCIFParser, is_aa

from src.config import Config
from src.models.protein_data_from_pdb import ProteinDataFromPDB

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


def parse_pdbx(pdb_id: str, config: Config) -> Optional[ProteinDataFromPDB]:
    logging.debug("[%s] PDB parsing started", pdb_id)
    filepath = os.path.join(config.path_to_pdb_files, f"{pdb_id}.cif")
    logging.debug("[%s] Will extract cif file from: %s", pdb_id, filepath)
    try:
        protein_data = _parse_pdbx_unsafe(pdb_id, filepath)
        return protein_data
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # We want to catch broad exception here so unforseen data error doesn't kill the whole test_data processing.
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return None


def _parse_pdbx_unsafe(pdb_id: str, filepath: str) -> ProteinDataFromPDB:
    protein_data = ProteinDataFromPDB(pdb_id=pdb_id)
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


def _is_water(residue: 'Residue') -> bool:
    return residue.resname == "HOH"


def _atom_list_contains_metal(atom_list: list['Atom']) -> bool:
    for atom in atom_list:
        if atom.element.lower() in METAL_ELEMENT_NAMES:
            return True
    return False
