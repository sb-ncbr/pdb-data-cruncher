import csv
import logging
import os.path

from pdbeccdutils.core import ccd_reader
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Lipinski

from src.models import LigandInfo
from src.exception import ParsingError
from src.models.ids_to_update import IdsToUpdateAndRemove


def parse_ligand_stats(ligand_stats_csv_path: str) -> dict[str, LigandInfo]:
    """
    Takes a csv with ligand stats and loads it into a dictionary.

    :param ligand_stats_csv_path: Path to the csv file with ligand stats.
    :return: Ligand stats from the csv loaded into dictionary.
    :raises OSError: When the file cannot be opened or read from.
    """
    ligand_stats_dict = {}
    first_row = True

    with open(ligand_stats_csv_path, encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")

        for row in reader:
            try:
                if first_row:
                    first_row = False
                    _check_first_ligand_row(row)
                else:
                    ligand_id, ligand_stats = _process_normal_ligand_stats_row(row)
                    ligand_stats_dict[ligand_id] = ligand_stats
            except ParsingError as ex:
                logging.warning("Skipping ligand stats row '%s', reason: %s", row, str(ex))

    logging.debug("Finished parsing ligand stats. Loaded %s ligands.", len(ligand_stats_dict))
    return ligand_stats_dict


def _check_first_ligand_row(row: list[str]) -> None:
    """
    Checks if the first row contains expected csv headers.

    :param row: One row extracted from the csv.
    """
    if len(row) != 3 or row[0] != "LigandID" or row[1] != "heavyAtomSize" or row[2] != "flexibility":
        raise ParsingError("Expected first line content 'LigandID;heavyAtomSize;flexibility'")


def _process_normal_ligand_stats_row(row: list[str]) -> tuple[str, LigandInfo]:
    """
    Validates contents of normal csv row and returns it processed.

    :param row: One row extracted from the csv.
    :return: Tuple consisting of ligand id and newly created LigandStats strucutre.
    """
    if len(row) != 3:
        raise ParsingError("Unexpected item count, expected 3 items.")

    try:
        return row[0], LigandInfo(row[0], int(row[1]), float(row[2]))
    except ValueError as ex:
        raise ParsingError(str(ex)) from ex


def calculate_ligand_stats(
    path_to_ccd_files: str, ids_to_update_and_remove: IdsToUpdateAndRemove
) -> list[LigandInfo]:
    """
    Calculate ligand stats for given ligand ids.
    :param path_to_ccd_files: Path to folder where all ligand cif files are.
    :param ids_to_update_and_remove: Inside contains ligand ids to update.
    :return: List of LigandInfo.
    """
    ligand_stats = []
    failed_ligand_ids = []
    for ligand_id in ids_to_update_and_remove.ligands_to_update:
        try:
            ligand_stats.append(_calculate_one_ligand_stats(path_to_ccd_files, ligand_id))
        except (AttributeError, OSError, ParsingError) as ex:
            logging.info("Failed to update ligand %s: %s", ligand_id, ex)
            failed_ligand_ids.append(ligand_id)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.warning("Failed to update ligand %s for unexpected reason: %s", ligand_id, ex)
            failed_ligand_ids.append(ligand_id)

    if failed_ligand_ids:
        logging.warning("Failed to update for %s ligand ids: %s", len(failed_ligand_ids), failed_ligand_ids)

    return ligand_stats


def _calculate_one_ligand_stats(path_to_ccd_files: str, ligand_id: str) -> LigandInfo:
    ligand_cif_path = os.path.join(path_to_ccd_files, f"{ligand_id}.cif")
    ligand_full_mol = ccd_reader.read_pdb_cif_file(ligand_cif_path).component.mol

    # TODO try to remove the try and just calculate it all - after comprehensive test
    try:
        ligand_mol_without_hs = Chem.RemoveHs(ligand_full_mol)
        rotatable_bond_count = rdMolDescriptors.CalcNumRotatableBonds(ligand_mol_without_hs, strict=False)
    except Chem.rdchem.AtomValenceException:
        rotatable_bond_count = _calculate_rotatable_bonds_for_faulty_atom_valence(ligand_full_mol)

    total_bonds = ligand_full_mol.GetNumBonds()

    return LigandInfo(
        id=ligand_id,
        heavy_atom_count=Lipinski.HeavyAtomCount(ligand_full_mol),
        flexibility=(rotatable_bond_count / total_bonds if total_bonds > 0 else 0),
    )


def _calculate_rotatable_bonds_for_faulty_atom_valence(ligand_full_mol: Chem.Mol) -> int:
    mol_withouth_hs: Chem.Mol = Chem.RemoveHs(ligand_full_mol, sanitize=False)
    bond_count = 0

    for bond in mol_withouth_hs.GetBonds():
        bond_type = bond.GetBondType()
        if bond_type == Chem.BondType.DOUBLE or bond_type == Chem.BondType.TRIPLE:
            continue  # double or triple bond cannot rotate
        if bond.GetBeginAtom().GetDegree() == 1 or bond.GetEndAtom().GetDegree() == 1:
            continue  # one of the atoms is terminal
        if bond.IsInRing():
            continue

        bond_count += 1

    return bond_count
