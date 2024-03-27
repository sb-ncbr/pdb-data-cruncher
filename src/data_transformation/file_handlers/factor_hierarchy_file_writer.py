import logging
import os
from typing import Any

from src.generic_file_handlers.json_file_writer import write_json_file
from src.utils import find_matching_files


FACTOR_HIERARCHY_SUFFIX = "FactorHierarchy.json"


def create_factor_hierarchy_file(
    updated_factor_hiearchy_json: Any, output_folder_path: str, current_date_prefix: str
) -> None:
    """
    Write factor hierarchy json into a file.
    :param updated_factor_hiearchy_json:
    :param output_folder_path:
    :param current_date_prefix: Current date formatted as 20240101 from the config to be used in filename.
    """
    filepath = os.path.join(output_folder_path, f"{current_date_prefix}_{FACTOR_HIERARCHY_SUFFIX}")
    write_json_file(filepath, updated_factor_hiearchy_json)
    logging.info("Saved updated factor hierarchy json into %s.", filepath)


def find_older_factor_hierarchy_file(output_folder_path: str) -> str:
    """
    Find older factor hierarchy file filepath for future updating.
    :return: Filepath to the found factor hierarchy file.
    """
    factor_hierarchy_files = find_matching_files(output_folder_path, FACTOR_HIERARCHY_SUFFIX)
    if len(factor_hierarchy_files) > 0:
        return os.path.join(output_folder_path, factor_hierarchy_files[0])
    return ""


def delete_old_factor_hierarchy_files(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Go throught the output directory, and delete all files matching factor hierarchy name, leave only those
    with given date in prefix.
    :param output_folder_path:
    :param current_date_prefix: String in format 20240101.
    :return:
    """
    factor_hierarchy_files = find_matching_files(output_folder_path, FACTOR_HIERARCHY_SUFFIX)
    for filename in factor_hierarchy_files:
        if current_date_prefix in filename:
            continue

        full_filepath = os.path.join(output_folder_path, filename)
        os.remove(full_filepath)
        logging.info("Deleted old '%s'.", full_filepath)
