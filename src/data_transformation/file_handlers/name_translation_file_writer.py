import logging
import os
from typing import Any

from src.generic_file_handlers.json_file_writer import write_json_file
from src.utils import find_matching_files


NAME_TRANSLATION_SUFFIX = "NameTranslation.json"


def create_name_translation_file(
    updated_name_translation_json: Any, output_folder_path: str, current_date_prefix: str
) -> None:
    """
    Write name translation json into a file.
    :param updated_name_translation_json:
    :param output_folder_path:
    :param current_date_prefix: Current date formatted as 20240101 from the config to be used in filename.
    """
    filepath = os.path.join(output_folder_path, f"{current_date_prefix}_{NAME_TRANSLATION_SUFFIX}")
    write_json_file(filepath, updated_name_translation_json)
    logging.info("Saved updated name translation json into %s.", filepath)


def delete_old_name_translation_files(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Go throught the output directory, and delete all files matching name translation name, leave only those
    with given date in prefix on no prefix at all.
    :param output_folder_path:
    :param current_date_prefix: String in format 20240101.
    :return:
    """
    name_translation_files = find_matching_files(output_folder_path, f"_{NAME_TRANSLATION_SUFFIX}")
    for filename in name_translation_files:
        if current_date_prefix in filename:
            continue

        full_filepath = os.path.join(output_folder_path, filename)
        os.remove(full_filepath)
        logging.info("Deleted old '%s'.", full_filepath)
