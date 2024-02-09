import csv
import logging

from src.models import LigandInfo
from src.exception import ParsingError


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
                    check_first_ligand_row(row)
                else:
                    ligand_id, ligand_stats = process_normal_ligand_stats_row(row)
                    ligand_stats_dict[ligand_id] = ligand_stats
            except ParsingError as ex:
                logging.warning("Skipping ligand stats row '%s', reason: %s", row, str(ex))

    logging.debug("Finished parsing ligand stats. Loaded %s ligands.", len(ligand_stats_dict))
    return ligand_stats_dict


def check_first_ligand_row(row: list[str]) -> None:
    """
    Checks if the first row contains expected csv headers.

    :param row: One row extracted from the csv.
    """
    if len(row) != 3 or row[0] != "LigandID" or row[1] != "heavyAtomSize" or row[2] != "flexibility":
        raise ParsingError("Expected first line content 'LigandID;heavyAtomSize;flexibility'")


def process_normal_ligand_stats_row(row: list[str]) -> tuple[str, LigandInfo]:
    """
    Validates contents of normal csv row and returns it processed.

    :param row: One row extracted from the csv.
    :return: Tuple consisting of ligand id and newly created LigandStats strucutre.
    """
    if len(row) != 3:
        raise ParsingError("Unexpected item count, expected 3 items.")

    try:
        return row[0], LigandInfo(int(row[1]), float(row[2]))
    except ValueError as ex:
        raise ParsingError(str(ex)) from ex
