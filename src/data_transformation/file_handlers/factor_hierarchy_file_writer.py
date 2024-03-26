import logging
from typing import Any
from os import path

from src.generic_file_handlers.json_file_writer import write_json_file
from src.utils import get_formatted_date


def create_factor_hierarchy_file(updated_factor_hiearchy_json: Any, output_folder_path: str) -> None:
    """
    Write factor hierarchy json into a file.
    :param updated_factor_hiearchy_json:
    :param output_folder_path:
    """
    filepath = path.join(output_folder_path, f"{get_formatted_date()}_FactorHierarchy.json")
    write_json_file(filepath, updated_factor_hiearchy_json)
    logging.info("Saved updated factor hierarchy json into %s.", filepath)
