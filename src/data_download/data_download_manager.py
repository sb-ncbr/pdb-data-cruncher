import logging
import os
from typing import Optional

from src.config import Config
from src.data_download.failing_ids_handler import get_failing_ids, update_failing_ids, FailedIdsSourceType
from src.data_download.ids_to_download_loader import load_overriden_ids_to_download
from src.data_download.ligand_ccd_handler import download_and_find_changed_ligand_cifs
from src.data_download.rest_download import RestDataType, download_one_type_rest_files
from src.data_download.rsync_handler import rsync_and_unzip, RsyncDataType
from src.exception import FileWritingError, ParsingError, DataDownloadError
from src.generic_file_handlers.json_file_loader import load_json_file
from src.generic_file_handlers.json_file_writer import write_json_file
from src.generic_file_handlers.simple_lock_handler import (
    check_no_lock_present_preventing_download, create_simple_lock_file, LockType
)
from src.models.ids_to_update import IdsToUpdateAndRemove, ChangedIds
from src.utils import ensure_folder_exists, delete_file_if_possible


class DownloadManager:
    """
    Class aggregating functions downlading data.
    """

    @staticmethod
    def ensure_download_target_folders_exist(config: Config) -> None:
        """
        Make sure folders for storing data that may not exist in the first run exist. But logging warning is
        issued in such case, to alert to the possibility of typo in file paths (as the app will almost never
        be run with empty data folder).
        :param config: App configuration.
        """
        ensure_folder_exists(config.filepaths.rest_jsons, True)
        for pdb_rest_type in ["assembly", "summary", "molecules", "publications", "related_publications"]:
            ensure_folder_exists(os.path.join(config.filepaths.rest_jsons, pdb_rest_type), True)
        ensure_folder_exists(config.filepaths.validator_db_results, True)
        ensure_folder_exists(config.filepaths.pdb_mmcifs, True)
        ensure_folder_exists(config.filepaths.gz_pdb_mmcifs, True)
        ensure_folder_exists(config.filepaths.ligand_cifs, True)
        ensure_folder_exists(config.filepaths.xml_reports, True)
        ensure_folder_exists(config.filepaths.gz_xml_reports, True)

    @staticmethod
    def sync_pdbe_mmcif_via_rsync(config: Config) -> Optional[ChangedIds]:
        """
        Rsync PDBe mmCIF files. Extract them.
        :param config: App configuration.
        :return: Lists of recieved and deleted files.
        """
        logging.info("Starting rsync of mmcif files.")
        try:
            rsync_log = rsync_and_unzip(
                RsyncDataType.ARCHIVE_MMCIF,
                config.filepaths.gz_pdb_mmcifs,
                config.filepaths.pdb_mmcifs,
            )
            changed_ids = ChangedIds(
                updated=rsync_log.get_successful_recieved_ids(),
                deleted=rsync_log.get_deleted_ids(),
            )
            logging.info("Rsync mmcif files finished successfully. Changed ids: %s", changed_ids)
            return changed_ids
        except DataDownloadError as ex:
            logging.error(ex)
            return ChangedIds()

    @staticmethod
    def update_ligand_cifs(config: Config) -> ChangedIds:
        """
        Update ligand cif files. The big ligand file is downloaded, cut into individual ligand cifs, and those
        are saved if they are different from those already saved.
        :param config: App configuration.
        :return: Recieved and deleted ligand ids.
        """
        logging.info("Starting updating of ligand (ccd) cif files.")
        try:
            changed_ids = download_and_find_changed_ligand_cifs(
                config.filepaths.ligand_cifs, config.timeouts.ligand_cifs_timeout_s
            )
            logging.info("Updating of ligand (ccd) cif files finished successfully. Changed ids: %s", changed_ids)
            return changed_ids
        except DataDownloadError as ex:
            logging.error("Failed to update ligand (ccd) cif files. %s", ex)
            return ChangedIds()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.error("Unexpected error. Failed to update ligand (ccd) cif files. %s", ex)
            return ChangedIds()

    # pylint: disable=too-many-arguments
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
            config,
            structure_ids,
            failed_ids_json,
            RestDataType.SUMMARY,
            FailedIdsSourceType.REST_SUMMARY,
            resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config,
            structure_ids,
            failed_ids_json,
            RestDataType.MOLECULES,
            FailedIdsSourceType.REST_MOLECULES,
            resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config,
            structure_ids,
            failed_ids_json,
            RestDataType.ASSEMBLY,
            FailedIdsSourceType.REST_ASSEMBLY,
            resolved_failed_ids
        )
        DownloadManager.download_one_rest(
            config,
            structure_ids,
            failed_ids_json,
            RestDataType.PUBLICATIONS,
            FailedIdsSourceType.REST_PUBLICATIONS,
            resolved_failed_ids
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
    def rsync_xml_validation_files(config: Config) -> list[str]:
        """
        Rsync XML validation files, and extract them.
        :param config: App configuration.
        :return: List of stucture ids that got rsynced (and extracted).
        """
        logging.info("Starting rsync of xml validation files.")
        try:
            rsync_log = rsync_and_unzip(
                RsyncDataType.XML_VALIDATION_REPORTS,
                config.filepaths.gz_xml_reports,
                config.filepaths.xml_reports,
            )
            logging.info("Rsync of validation xml files finished successfully.")
            return rsync_log.get_successful_recieved_ids()
        except DataDownloadError as ex:
            logging.error(ex)
            return []

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
    def download_non_mmcif_files(config: Config, structure_ids: list[str]) -> bool:
        """
        Download other files, based on which mmcif files were updated. This includes all rest files, vdb reports
        and validation xmls.
        :param config:
        :param structure_ids:
        :return:
        """
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
        DownloadManager.download_validator_db_reports(config, structure_ids, failed_ids_json, prev_failed_that_passed)
        updated_xml_ids = DownloadManager.rsync_xml_validation_files(config)

        for structure_id_list in [prev_failed_that_passed, updated_xml_ids]:
            for structure_id in structure_id_list:
                # add previously failed ids that now suceeded to those that need to be updated during extraction as well
                if structure_id not in structure_ids:
                    structure_ids.append(structure_id)

        if previous_failed_ids_json_ok:
            try:
                write_json_file(config.filepaths.download_failed_ids_to_retry_json, failed_ids_json)
                return True
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

        return False

    @staticmethod
    def delete_old_non_mmcif_files(config: Config, deleted_structures_ids: list[str]) -> None:
        """
        Removes files from other data sources (rest, vdb reports) for which the mmcif file has been deleted.
        :param config:
        :param deleted_structures_ids:
        """
        logging.info("Deleting files for ids that were removed from mmcifs.")
        for structure_id in deleted_structures_ids:
            # rest files
            delete_file_if_possible(os.path.join(config.filepaths.rest_jsons, "summary", f"{structure_id}.json"))
            delete_file_if_possible(os.path.join(config.filepaths.rest_jsons, "assembly", f"{structure_id}.json"))
            delete_file_if_possible(os.path.join(config.filepaths.rest_jsons, "molecules", f"{structure_id}.json"))
            delete_file_if_possible(os.path.join(config.filepaths.rest_jsons, "publications", f"{structure_id}.json"))
            delete_file_if_possible(
                os.path.join(config.filepaths.rest_jsons, "related_publications", f"{structure_id}.json")
            )
            # vdb file
            delete_file_if_possible(os.path.join(config.filepaths.validator_db_results, structure_id, "result.json"))
        logging.info("Finished deleting files for ids that were removed from mmcifs.")

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
    logging.info("PHASE DATA DOWNLOAD is starting")
    check_no_lock_present_preventing_download(config)
    DownloadManager.ensure_download_target_folders_exist(config)

    if config.override_ids_to_download_filepath:
        changed_structure_ids = load_overriden_ids_to_download(config.override_ids_to_download_filepath)
    else:
        changed_structure_ids = DownloadManager.sync_pdbe_mmcif_via_rsync(config)

    if changed_structure_ids is None:
        return False

    changed_ligand_ids = DownloadManager.update_ligand_cifs(config)

    success = True

    success &= DownloadManager.download_non_mmcif_files(config, changed_structure_ids.updated)
    DownloadManager.delete_old_non_mmcif_files(config, changed_structure_ids.deleted)
    success &= DownloadManager.save_changed_ids_into_json(config, changed_structure_ids, changed_ligand_ids)

    create_simple_lock_file(LockType.DATA_EXTRACTION, config.filepaths.logs_root_path)

    logging.info("PHASE DATA DOWNLOAD finished")
    return success
