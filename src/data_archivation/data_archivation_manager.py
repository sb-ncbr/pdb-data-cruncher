import logging
import subprocess
from os import path

from src.config import Config
from src.exception import DataArchivationError


# pylint: disable=too-few-public-methods
class DataArchivationManger:
    """
    Class aggregating methods for archive creation and handling.
    """

    @staticmethod
    def update_archive(archive_filepath: str, folder_to_archive_path: str) -> None:
        """
        Updates the archive via 7z commandline utility.
        :param archive_filepath:
        :param folder_to_archive_path:
        """
        logging.info("Starting to update archive %s with data from %s.", archive_filepath, folder_to_archive_path)
        # u => update the archive
        # -uq0 => defines behaviour for files that exist in the archive but not in data to archive as: delete in archive
        command = ["7z", "u", archive_filepath, "-uq0", folder_to_archive_path]
        logging.debug("Running command: %s", " ".join(command))
        try:
            subprocess.run(command, check=True, capture_output=True)
            logging.info("Successfully updated archive %s", archive_filepath)
        except subprocess.CalledProcessError as ex:
            logging.error("\n%s\n", ex.stderr.decode("utf8").strip())
            raise DataArchivationError(
                f"Failed to update '{archive_filepath}' with data from {folder_to_archive_path}: {ex}"
            ) from ex


def run_data_archivation(config: Config) -> bool:
    """
    Updates 7zip archives with pdb id set (defined by data download phase or config values).
    :param config: Application configuration.
    :return: True if action succeeded. False otherwise.
    """
    logging.info("Running data archivation.")
    data_to_archive = [  # source folder and resulting archive name
        (config.filepaths.pdb_mmcifs, "rawpdbe.7z"),
        (config.filepaths.xml_reports, "rawvalidxml.7z"),
        (config.filepaths.rest_jsons, "rawrest.7z"),
        (config.filepaths.validator_db_results, "rawvdb.7z"),
        (config.filepaths.ligand_cifs, "rawccd.7z")
    ]
    failed_count = 0

    for data_source_folder, final_archive_name in data_to_archive:
        archive_path = path.join(config.filepaths.output_root_path, final_archive_name)
        try:
            DataArchivationManger.update_archive(archive_path, data_source_folder)
        except DataArchivationError as ex:
            logging.error(ex)
            failed_count += 1

    if failed_count > 0:
        logging.error("%s folders failed to be archived.", failed_count)
        return False

    logging.info("Data archivation finished successfully.")
    return True
