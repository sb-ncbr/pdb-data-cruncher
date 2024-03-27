import logging
import os

import py7zr

from src.exception import FileWritingError


def create_archive_of_folder(folder_to_archive_filepath: str, output_folder_filepath: str, archive_name: str) -> None:
    """
    Archive given folder into .7z format archive.
    :param folder_to_archive_filepath: Path to the folder to archive.
    :param output_folder_filepath: Path to folder where the ouput should be stored.
    :param archive_name: Name of the created archive.
    """
    if not os.path.isdir(folder_to_archive_filepath):
        raise FileWritingError(f"Path to archive '{folder_to_archive_filepath}' does not point to a folder.")

    archive_filepath = path.join(output_folder_filepath, archive_name)
    _, folder_to_archive_name = path.split(path.dirname(folder_to_archive_filepath))
    with py7zr.SevenZipFile(archive_filepath, "w") as archive:
        archive.writeall(folder_to_archive_filepath, folder_to_archive_name)

    logging.info("Saved folder '%s' as archive '%s'.", folder_to_archive_filepath, archive_filepath)
