import logging
import os
from typing import Optional

from src.config import Config
from src.data_download.failing_ids_handler import get_failing_ids, update_failing_ids, FailedIdsSourceType
from src.exception import FileWritingError, ParsingError, DataDownloadError
from src.data_download.rest_download import RestDataType, download_one_type_rest_files
from src.data_download.ligand_ccd_handler import download_and_find_changed_ligand_cifs
from src.data_download.rsync_handler import RsyncLog, rsync_folder
from src.generic_file_handlers.json_file_loader import load_json_file
from src.generic_file_handlers.json_file_writer import write_json_file
from src.generic_file_handlers.simple_lock_handler import (
    check_no_lock_present_preventing_download
)
from src.models.ids_to_update import IdsToUpdateAndRemove, ChangedIds
from src.utils import ensure_folder_exists


class DownloadManager:
    @staticmethod
    def ensure_download_target_folders_exist(config: Config) -> None:
        ensure_folder_exists(config.filepaths.rest_jsons, True)
        for pdb_rest_type in ["assembly", "summary", "molecules", "publications", "related_publications"]:
            ensure_folder_exists(os.path.join(config.filepaths.rest_jsons, pdb_rest_type), True)
        ensure_folder_exists(config.filepaths.validator_db_results, True)
        ensure_folder_exists(config.filepaths.pdb_mmcifs, True)
        ensure_folder_exists(config.filepaths.ligand_cifs, True)
        ensure_folder_exists(config.filepaths.xml_reports, True)

    @staticmethod
    def sync_pdbe_mmcif_via_rsync(config: Config) -> Optional[ChangedIds]:
        logging.info("Starting sync of pdbe mmcif files via rsync.")
        try:
            rsync_log = rsync_folder(config.filepaths.pdb_mmcifs)
            logging.info("Rsync of pdbe mmcif files finished successfully.")
            return ChangedIds()
        except DataDownloadError as ex:
            logging.error(ex)
            return None

    @staticmethod
    def update_ligand_cifs(config: Config) -> ChangedIds:
        logging.info("Starting updating of ligand (ccd) cif files.")
        try:
            changed_ids = download_and_find_changed_ligand_cifs(
                config.filepaths.ligand_cifs, config.timeouts.ligand_cifs_timeout_s
            )
            logging.info("Updating of ligand (ccd) cif files finished successfully.")
            return changed_ids
        except DataDownloadError as ex:
            logging.error("Failed to update ligand (ccd) cif files. %s", ex)
            return ChangedIds()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.error("Unexpected error. Failed to update ligand (ccd) cif files. %s", ex)
            return ChangedIds()

    @staticmethod
    def download_one_rest(
        config: Config,
        ids_to_download: list[str],
        failed_ids_json: dict,
        rest_data_type: RestDataType,
        failed_ids_source_type: FailedIdsSourceType,
        resolved_failed_ids: list[str],
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
        :param resolved_failed_ids:
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

        for previously_failed_id in ids_to_retry:
            if previously_failed_id not in failed_ids:
                resolved_failed_ids.append(previously_failed_id)

        update_failing_ids(failed_ids_json, failed_ids_source_type, failed_ids)

    @staticmethod
    def download_rest_files(
        config: Config, structure_ids: list[str], failed_ids_json: dict, resolved_failed_ids: list[str]
    ) -> None:
        """
        Download rest files for all types (summary, molecules, assembly, publications and related publications).
        Downloads those for given ids + those with ids loaded from json holding ids that failed last time the app
        was run. The failed ids json is then updated with ids that failed (and those previously there that
        succeeded are removed).
        :param config:
        :param structure_ids:
        :param failed_ids_json:
        :param resolved_failed_ids: List of ids where those that previously failed but now succeed should be appended.
        """
        logging.info("Starting downloading rest files.")
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.SUMMARY, FailedIdsSourceType.REST_SUMMARY, resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.MOLECULES, FailedIdsSourceType.REST_MOLECULES, resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.ASSEMBLY, FailedIdsSourceType.REST_ASSEMBLY, resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config, structure_ids, failed_ids_json, RestDataType.PUBLICATIONS, FailedIdsSourceType.REST_PUBLICATIONS, resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config,
            structure_ids,
            failed_ids_json,
            RestDataType.RELATED_PUBLICATIONS,
            FailedIdsSourceType.REST_RELATED_PUBLICATIONS,
            resolved_failed_ids,
        )
        logging.info("Finished downloading rest files.")

    @staticmethod
    def download_xml_validation_files(config: Config, structure_ids: list[str], failed_ids_json: dict) -> None:
        ids_to_retry = get_failing_ids(failed_ids_json, FailedIdsSourceType.XML_VALIDATION)
        logging.info("TODO this will download xml validation files for %s", structure_ids)  # TODO

    @staticmethod
    def download_validator_db_reports(
        config: Config, structure_ids: list[str], failed_ids_json: dict, resolved_failed_ids: list[str]
    ) -> None:
        """
        Download validator db reports. Include failed ids from previous runs, and add newly failed ids to the
        failed ids json.
        :param config:
        :param structure_ids:
        :param failed_ids_json:
        :param resolved_failed_ids:
        """
        logging.info("Starting downloading validator db reports.")
        DownloadManager.download_one_rest(
            config, structure_ids,
            failed_ids_json,
            RestDataType.VALIDATOR_DB,
            FailedIdsSourceType.VALIDATOR_DB_REPORT,
            resolved_failed_ids,
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

        prev_failed_that_passed = []

        DownloadManager.download_rest_files(config, structure_ids, failed_ids_json, prev_failed_that_passed)
        DownloadManager.download_xml_validation_files(config, structure_ids, failed_ids_json)
        DownloadManager.download_validator_db_reports(config, structure_ids, failed_ids_json, prev_failed_that_passed)

        for structure_id in prev_failed_that_passed:
            # add previously failed ids that now suceeded to those that need to be updated during extraction as well
            if structure_id not in structure_ids:
                structure_ids.append(structure_id)

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
    DownloadManager.ensure_download_target_folders_exist(config)
    overall_success = True  # TODO some other may need this, flow not done

    if config.override_ids_to_download_filepath:
        updated_ids = _load_ids_to_download(config.override_ids_to_download_filepath)
        if updated_ids is None:
            return False
        logging.info("Override for ids to download was set, will update structures: %s", updated_ids)
        changed_structure_ids = ChangedIds(
            updated=updated_ids,
            deleted=[],
        )
    else:
        changed_structure_ids = DownloadManager.sync_pdbe_mmcif_via_rsync(config)
        if changed_structure_ids is None:
            return False

    # TODO switch back
    # changed_ligand_ids = DownloadManager.update_ligand_cifs(config)
    changed_ligand_ids = ChangedIds()

    # TODO delete those that are to be deleted
    DownloadManager.download_non_mmcif_files(config, changed_structure_ids.updated)
    overall_success &= DownloadManager.save_changed_ids_into_json(config, changed_structure_ids, changed_ligand_ids)
    # TODO uncomment the lock file -> removed just for testing
    # create_simple_lock_file(LockType.DATA_EXTRACTION, config)

    return overall_success


def _load_ids_to_download(list_of_ids_path: str) -> Optional[list[str]]:
    try:
        ids_json = load_json_file(list_of_ids_path)
        if not isinstance(ids_json, list) or [item for item in ids_json if not isinstance(item, str)]:
            logging.error("Loaded json %s with ids to update is not a list of strings.", ids_json)
            return None
        return ids_json
    except ParsingError as ex:
        logging.error("Failed loading ids to download from json %s: %s", list_of_ids_path, ex)
        return None
