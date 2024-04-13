import logging
from dataclasses import dataclass, field

from src.config import Config
from src.data_download.failing_ids_handler import get_failing_ids, update_failing_ids, FailedIdsSourceType
from src.exception import FileWritingError, ParsingError
from src.data_download.rest_download import RestDataType, download_one_type_rest_files
from src.generic_file_handlers.json_file_loader import load_json_file
from src.generic_file_handlers.json_file_writer import write_json_file
from src.generic_file_handlers.simple_lock_handler import (
    check_no_lock_present_preventing_download, create_simple_lock_file, LockType
)
from src.models.ids_to_update import IdsToUpdateAndRemove


@dataclass
class ChangedIds:
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


class DownloadManager:
    @staticmethod
    def sync_pdbe_mmcif_via_rsync(config: Config) -> ChangedIds:
        logging.info("Starting sync of pdbe mmcif files via rsync.")
        # TODO
        logging.info("Rsync of pdbe mmcif files finished successfully.")
        return ChangedIds()

    @staticmethod
    def update_ligand_cifs(config: Config) -> ChangedIds:
        logging.info("Starting updating of ligand (ccd) cif files.")
        # TODO
        logging.info("Updating of ligand (ccd) cif files finished successfully.")
        return ChangedIds()

    @staticmethod
    def download_one_rest(
        config: Config,
        ids_to_download: list[str],
        failed_ids_json: dict,
        rest_data_type: RestDataType,
        failed_ids_source_type: FailedIdsSourceType,
    ) -> None:
        """
        Download rest files for one type (summary, molecules, assembly, publications or related publications).
        Downloads those for given ids + those with ids loaded from json holding ids that failed last time the app
        was run. The failed ids json is then updated with ids that failed (and those previously there that
        succeeded are removed).
        :param config:
        :param ids_to_download:
        :param failed_ids_json:
        :param rest_data_type:
        :param failed_ids_source_type:
        """
        if rest_data_type == RestDataType.VALIDATOR_DB:
            root_json_folder = config.filepaths.validator_db_results
        else:
            root_json_folder = config.filepaths.rest_jsons

        ids_to_retry = get_failing_ids(failed_ids_json, failed_ids_source_type)
        failed_ids = download_one_type_rest_files(
            set(ids_to_download + ids_to_retry),
            rest_data_type,
            root_json_folder,
            config.timeouts.rest_timeout_s,
        )
        update_failing_ids(failed_ids_json, failed_ids_source_type, failed_ids)

    @staticmethod
    def download_rest_files(config: Config, structure_ids: list[str], failed_ids_json: dict) -> None:
        """
        Download rest files for all types (summary, molecules, assembly, publications and related publications).
        Downloads those for given ids + those with ids loaded from json holding ids that failed last time the app
        was run. The failed ids json is then updated with ids that failed (and those previously there that
        succeeded are removed).
        :param config:
        :param structure_ids:
        :param failed_ids_json:
        """
        logging.info("Starting downloading rest files.")
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.SUMMARY, FailedIdsSourceType.REST_SUMMARY
        )
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.MOLECULES, FailedIdsSourceType.REST_MOLECULES
        )
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.ASSEMBLY, FailedIdsSourceType.REST_ASSEMBLY
        )
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.PUBLICATIONS, FailedIdsSourceType.REST_PUBLICATIONS
        )
        DownloadManager.download_one_rest(
            config,
            structure_ids,
            failed_ids_json,
            RestDataType.RELATED_PUBLICATIONS,
            FailedIdsSourceType.REST_RELATED_PUBLICATIONS
        )
        logging.info("Finished downloading rest files.")

    @staticmethod
    def download_xml_validation_files(config: Config, structure_ids: list[str], failed_ids_json: dict) -> None:
        ids_to_retry = get_failing_ids(failed_ids_json, FailedIdsSourceType.XML_VALIDATION)
        logging.info("TODO this will download xml validation files for %s", structure_ids)  # TODO

    @staticmethod
    def download_validator_db_reports(config: Config, structure_ids: list[str], failed_ids_json: dict) -> None:
        """
        Download validator db reports. Include failed ids from previous runs, and add newly failed ids to the
        failed ids json.
        :param config:
        :param structure_ids:
        :param failed_ids_json:
        """
        logging.info("Starting downloading validator db reports.")
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.VALIDATOR_DB, FailedIdsSourceType.VALIDATOR_DB_REPORT
        )
        logging.info("Finished downloading validator db reports.")

    @staticmethod
    def download_non_mmcif_files(config: Config, structure_ids: list[str]) -> None:
        previous_failed_ids_json_ok = True
        try:
            failed_ids_json = load_json_file(
                config.filepaths.download_failed_ids_to_retry_json,
                raise_on_file_not_found=False,
                default_if_not_found={}
            )
        except ParsingError as ex:
            previous_failed_ids_json_ok = False
            failed_ids_json = {}
            logging.error("Failed to load failed_ids_json: %s", ex)

        DownloadManager.download_rest_files(config, structure_ids, failed_ids_json)
        DownloadManager.download_xml_validation_files(config, structure_ids, failed_ids_json)
        DownloadManager.download_validator_db_reports(config, structure_ids, failed_ids_json)

        if previous_failed_ids_json_ok:
            try:
                write_json_file(config.filepaths.download_failed_ids_to_retry_json, failed_ids_json)
            except FileWritingError as ex:
                logging.critical(
                    "Saving failed ids into json failed! %s. Any ids not there would be removed. Check why the saving "
                    "failed, and manually overwrite the file with:\n%s",
                    ex,
                    failed_ids_json
                )
        else:
            logging.critical(
                "Because loading failed ids json from previous download failed, new information is not overwriten. "
                "Check the integrity of the file. Following ids failed this run:\n%s\nAdd it to existing failed ids "
                "json or create new one, otherwise this information will be lost!",
                failed_ids_json
            )

    @staticmethod
    def save_changed_ids_into_json(config: Config, changed_structures: ChangedIds, changed_ligands: ChangedIds) -> bool:
        """
        Save changed ids into json for further data extraction. In case of fatal error, this information is output
        into log.
        :param config:
        :param changed_structures:
        :param changed_ligands:
        :return: True if successfull, False if not.
        """
        try:
            ids_to_update_and_remove = IdsToUpdateAndRemove(
                structures_to_update=changed_structures.updated,
                structures_to_delete=changed_structures.deleted,
                ligands_to_update=changed_ligands.updated,
                ligands_to_delete=changed_ligands.deleted,
            )

            write_json_file(config.filepaths.download_changed_ids_json, ids_to_update_and_remove.to_dict())
            return True
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.critical("Failed to save ids that changed from rsync! Reason: %s.", ex)
            logging.error(
                "Structure ids that changed: %s.\nLigand ids that changed: %s,\nThis information will be lost! To "
                "prevent that, save it into json (check user guide) and run app with SKIP_DOWNLOAD on.",
                changed_structures,
                changed_ligands,
            )
            return False


def run_data_download(config: Config) -> bool:
    """
    Download new data and create files with changed pdb ids.
    :param config: Application configuration.
    :return: True if action succeeded. False otherwise.
    """
    check_no_lock_present_preventing_download(config)

    overall_success = True  # TODO some other may need this, flow not done

    changed_structure_ids = DownloadManager.sync_pdbe_mmcif_via_rsync(config)
    changed_ligand_ids = DownloadManager.sync_pdbe_mmcif_via_rsync(config)

    # TODO remove this
    changed_structure_ids = ChangedIds(
        updated=["1dey", "3rec", "8ucv"]
    )

    overall_success &= DownloadManager.save_changed_ids_into_json(config, changed_structure_ids, changed_ligand_ids)
    # TODO uncomment the lock file -> removed just for testing
    # create_simple_lock_file(LockType.DATA_EXTRACTION, config)
    DownloadManager.download_non_mmcif_files(config, changed_structure_ids.updated)
    return overall_success
