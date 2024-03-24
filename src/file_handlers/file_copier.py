import logging
from os import path
import shutil

from src.exception import FileWritingError


def copy_file_to_output_files(original_file_path: str, new_location_folder: str, new_file_name: str) -> None:
    """
    Copies file. Assembles the path to where it should be copied.
    :param original_file_path:
    :param new_location_folder:
    :param new_file_name:
    """
    output_file_filepath = path.join(new_location_folder, new_file_name)
    try:
        shutil.copyfile(original_file_path, output_file_filepath)
        logging.info("Copied file '%s' to '%s'.", original_file_path, output_file_filepath)
    except OSError as ex:
        raise FileWritingError(f"Failed to copy file: {ex}") from ex
