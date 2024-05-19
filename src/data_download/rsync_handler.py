import gzip
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.exception import DataDownloadError


@dataclass(slots=True)
class RsyncLogItem:
    """
    Single item from parsed rsync log.
    """

    relative_path: str
    filename: str
    structure_id: Optional[str] = "????"
    unpacking_failure: bool = False


@dataclass(slots=True)
class RsyncLog:
    """
    Parsed rsync log.
    """

    recieved: list[RsyncLogItem] = field(default_factory=list)
    deleted: list[RsyncLogItem] = field(default_factory=list)

    def get_successful_recieved_ids(self) -> list[str]:
        """
        Get list of recieved structure ids considered successful (where unpacking did not fail).
        :return: List of strings representing structure ids (without file extensions).
        """
        return [
            rsync_log_item.structure_id
            for rsync_log_item
            in self.recieved
            if not rsync_log_item.unpacking_failure
        ]

    def get_deleted_ids(self) -> list[str]:
        """
        Get list of structure ids that were deleted.
        :return: List of strings representing structure ids (without file extensions).
        """
        return [
            rsync_log_item.structure_id
            for rsync_log_item
            in self.deleted
        ]


class RsyncDataType(Enum):
    """
    Type of data to rsync.
    """

    ARCHIVE_MMCIF = 0
    XML_VALIDATION_REPORTS = 1


def rsync_and_unzip(rsync_data_type: RsyncDataType, gzip_folder: str, unpacked_folder: str) -> RsyncLog:
    """
    Assembles rsync command based on rsync data type. Runs the command. Parses the rsync log to get recieved
    and deleted files entries. Unzips the gz from the files for recieved files, removes the removed from unzipped.
    :param rsync_data_type: Type of data to rsync. Rsync command is assembled based on it, and logs are parsed
    differently for each type (based on file extensions associated with the type).
    :param gzip_folder: Path to folder where .gz versions are stored. This is the rsync target.
    :param unpacked_folder: Folder where unpacked files are stored.
    :return: Parsed rsync log.
    """
    rsync_command = _assemble_rsync_command(rsync_data_type, gzip_folder)
    logging.info("Running rsync command: '%s'", " ".join(rsync_command))
    rsync_raw_log = _run_rsync_command(rsync_command)
    logging.info("Rsync of gzip files done. Next: parsing log.")

    if rsync_data_type == RsyncDataType.ARCHIVE_MMCIF:
        rsync_log = _parse_rsync_log_for_mmcif(rsync_raw_log)
    elif rsync_data_type == RsyncDataType.XML_VALIDATION_REPORTS:
        rsync_log = _parse_rsync_log_for_xml_validation(rsync_raw_log)
    else:
        raise DataDownloadError(f"Unsupported rsync type {rsync_data_type}.")

    logging.info("Parsing rsync log finished. Next: unzipping new data.")
    _gunzip_updated_files(rsync_log.recieved, gzip_folder, unpacked_folder)
    logging.info("Unzipping new data finished. Next: deleting unzipped files not present in .gz files anymore.")
    _delete_removed_files(rsync_log.deleted, unpacked_folder)

    logging.info("Finished deleting old unzipped files.")
    return rsync_log


def _assemble_rsync_command(rsync_data_type: RsyncDataType, target_folder_path: str) -> list[str]:
    command = [
        "rsync",
        "-rLtz",
        "--delete",
        '--out-format="%o %f"',
        "--port=33444",
    ]

    if rsync_data_type == RsyncDataType.ARCHIVE_MMCIF:
        command.extend([
            "rsync.rcsb.org::ftp_data/structures/all/mmCIF/",
        ])
    elif rsync_data_type == RsyncDataType.XML_VALIDATION_REPORTS:
        command.extend([
            "--exclude",
            "*multipercentile*",
            "--exclude",
            "*.pdf.gz",
            "--exclude",
            "*.cif.gz",
            "--exclude",
            "*map_coef*",
            "rsync.rcsb.org::ftp/validation_reports/",
        ])
    else:
        raise DataDownloadError(f"Unsupported rsync type {rsync_data_type}.")

    command.append(target_folder_path)
    return command


def _run_rsync_command(rsync_command: list[str]) -> str:
    try:
        completed_process = subprocess.run(rsync_command, check=True, capture_output=True)
        return completed_process.stdout.decode("utf8", errors="ignore")
    except subprocess.CalledProcessError as ex:
        logging.error(
            "Called subproccess error:\n%s\n",
            ex.stderr.decode("utf8", errors="ignore").strip(),
        )
        logging.critical(
            "Check the following log. If any items were recieved, manual actions are needed (unzipping the recieved "
            "files; and running download with overriden ids to download for these in case of mmcifs).\n%s\n",
            ex.stdout.decode("utf8", errors="ignore").strip(),
        )
        raise DataDownloadError(f"Rsync failed: {ex}") from ex


def _parse_rsync_log_for_xml_validation(rsync_raw_log: str) -> RsyncLog:
    rsync_log = _parse_rsync_log(rsync_raw_log, "_validation.xml.gz")

    for rsync_item_list in [rsync_log.recieved, rsync_log.deleted]:
        for rsync_item in rsync_item_list:
            rsync_item.structure_id = rsync_item.filename.replace("_validation.xml.gz", "")

    return rsync_log


def _parse_rsync_log_for_mmcif(rsync_raw_log: str) -> RsyncLog:
    rsync_log = _parse_rsync_log(rsync_raw_log, ".cif.gz")

    for rsync_item_list in [rsync_log.recieved, rsync_log.deleted]:
        for rsync_item in rsync_item_list:
            rsync_item.structure_id = rsync_item.filename.replace(".cif.gz", "")

    return rsync_log


def _parse_rsync_log(text_to_parse: str, only_lines_with_string: str) -> RsyncLog:
    """
    Load rsync log produced with formatting "%o %f" as list of recieved files and deleted files. Take only lines
    containing passed string.
    :param text_to_parse:
    :param only_lines_with_string:
    :return: RsyncLog instance.
    """
    rsync_log = RsyncLog()

    for line in text_to_parse.split(os.linesep):
        if only_lines_with_string not in line:
            continue

        split_line = line.replace('"', "").split(" ")
        if len(split_line) != 2:
            logging.error("Log line '%s' failed to process! This info will be lost, unless processed manually.", line)

        operation, filepath = split_line
        filename = filepath.split(os.path.sep)[-1]
        log_item = RsyncLogItem(relative_path=filepath, filename=filename)

        if operation in ["del", "del."]:
            rsync_log.deleted.append(log_item)
        elif operation == "recv":
            rsync_log.recieved.append(log_item)
        else:
            logging.error(
                "Unexpected operation '%s' in line '%s'. If this line is valid, the info is lost! Manual action needed",
                operation,
                line
            )

    return rsync_log


def _gunzip_updated_files(recieved_items: list[RsyncLogItem], gzip_folder: str, unpacked_folder: str) -> None:
    for item in recieved_items:
        source_path = os.path.join(gzip_folder, item.relative_path)
        destination_path = os.path.join(unpacked_folder, item.filename.replace(".gz", ""))
        try:
            _gunzip_one_file(source_path, destination_path)
        except DataDownloadError as ex:
            item.unpacking_failure = True
            logging.critical(
                "Structure %s rsynced, but failed to unzip. Manual action needed. %s", item.relative_path, ex
            )


def _gunzip_one_file(gz_filepath: str, unpacked_filepath: str) -> None:
    try:
        with gzip.open(gz_filepath, "rb") as input_file:
            with open(unpacked_filepath, "wb") as output_file:
                shutil.copyfileobj(input_file, output_file)
    except OSError as ex:
        raise DataDownloadError(f"Failed to unpack gz file: {ex}") from ex


def _delete_removed_files(deleted_items: list[RsyncLogItem], unpacked_folder: str) -> None:
    for item in deleted_items:
        old_filepath = os.path.join(unpacked_folder, item.filename.replace(".gz", ""))
        try:
            os.remove(old_filepath)
        except OSError as ex:
            logging.warning("Failed to delete %s. Consider deleting it manually. %s", old_filepath, ex)
