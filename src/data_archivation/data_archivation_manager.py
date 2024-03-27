import logging
from multiprocessing import Pool

from src.data_archivation.seven_zip_archive_creator import create_archive_of_folder
from src.config import Config


class DataArchivationManger:
    # TODO redo the functionality in incremental manner

    @staticmethod
    def create_7z_data_files(config: Config) -> None:
        """
        Create 7z archives from downloaded data.
        :param config: App configuration.
        """
        # TODO do only for changed files
        logging.info("Starting creation of 7z archives.")

        archive_creation_settings = [  # source folder and resulting archive name
            (config.path_to_pdbx_files, "rawpdbe.7z"),
            (config.path_to_xml_reports, "rawvalidxml.7z"),
            (config.path_to_rest_jsons, "rawrest.7z"),
            (config.path_to_validator_db_results, "rawvdb.7z"),
        ]

        # spawns process for each 7z archive task
        with Pool(config.max_process_count_in_multiprocessing) as p:
            p.starmap(
                create_archive_of_folder, [
                    (path_to_folder, config.output_root_path, archive_name)
                    for path_to_folder, archive_name
                    in archive_creation_settings
                ]
            )
        logging.info("Creation of 7z archives finished successfully.")