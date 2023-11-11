import csv
import logging

from src.classes import LigandStats
from src.exception import FileContentParsingError


# TODO raises OSError if file cannot be opened/read from, catch and process wherever this gets called
def load_ligand_stats(ligand_stats_csv_path: str) -> dict[str, LigandStats]:
    """
    Takes a csv with ligand stats and loads it into a dictionary.

    :param ligand_stats_csv_path: Path to the csv file with ligand stats.
    :return: Ligand stats from the csv loaded into dictionary.
    """
    ligand_stats_dict = {}
    first_row = True

    with open(ligand_stats_csv_path, encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")

        for row in reader:
            try:
                if first_row:
                    first_row = False
                    check_first_ligand_row(row)
                else:
                    ligand_id, ligand_stats = process_normal_ligand_stats_row(row)
                    ligand_stats_dict[ligand_id] = ligand_stats
            except FileContentParsingError as ex:
                logging.warning("Skipping ligand stats row '%s', reason: %s", row, str(ex))

    logging.debug("Loaded %s ligands.", len(ligand_stats_dict))
    return ligand_stats_dict


def check_first_ligand_row(row: list[str]) -> None:
    """
    Checks if the first row contains expected csv headers.

    :param row: One row extracted from the csv.
    """
    if len(row) != 3 or row[0] != "LigandID" or row[1] != "heavyAtomSize" or row[2] != "flexibility":
        raise FileContentParsingError("Expected first line content 'LigandID;heavyAtomSize;flexibility'")


def process_normal_ligand_stats_row(row: list[str]) -> tuple[str, LigandStats]:
    """
    Validates contents of normal csv row and returns it processed.

    :param row: One row extracted from the csv.
    :return: Tuple consisting of ligand id and newly created LigandStats strucutre.
    """
    if len(row) != 3:
        raise FileContentParsingError("Unexpected item count, expected 3 items.")

    try:
        return row[0], LigandStats(int(row[1]), float(row[2]))
    except ValueError as ex:
        raise FileContentParsingError(str(ex)) from ex
