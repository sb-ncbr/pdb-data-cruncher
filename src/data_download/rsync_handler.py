import logging
import os
import subprocess
from dataclasses import dataclass, field

from src.exception import ParsingError, DataDownloadError


TEMP_LOG_FILE_NAME = "temporary_rsync_log.txt"


@dataclass(slots=True)
class RsyncLog:
    """
    Representation of information from rsync log.
    """

    recieved: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


def rsync_xml_validation(xml_validation_folder: str, con_timeout_s: int, file_transfer_timeout_s: int) -> RsyncLog:
    # TODO work in progress
    # TODO remove the dry run
    command = [
        "rsync",
        "-rLtz",
        "--delete",
        "--dry-run",
        '--out-format="%o %f"',
        "--port=33444",
        f"--contimeout={con_timeout_s}",
        f"--timeout={file_transfer_timeout_s}",
        "rsync.rcsb.org::ftp/validation_reports/",
        xml_validation_folder,

    ]
    logging.info("Running command: %s", command)

    try:
        completed_process = subprocess.run(command, check=True, capture_output=True)
        rsync_raw_log = completed_process.stdout.decode("utf8", errors="ignore")
    except subprocess.CalledProcessError as ex:
        logging.error("\n%s\n", ex.stderr.decode("utf8", errors="ignore").strip())
        raise DataDownloadError(f"Failed to rsync mmcif files: {ex}. {ex}") from ex

    try:
        return parse_rsync_log(rsync_raw_log, file_ending_to_cut=".cif.gz")
    except ParsingError as ex:
        logging.critical(
            "Failed to parse rsync log, after rsync finished successfully. Files have been updated,"
            "but the information about which failed to be processed! Check the following output, and"
            "adjust ids to be redownloaded json to finish downloading for these files and run download only."
            "Then, create json with ids to update and remove for data extraction phase, and run that phase only."
            "Reason parsing failed: %s.",
            ex
        )
        logging.critical(rsync_raw_log)
        raise DataDownloadError(f"Failed to process rsync log. {ex}") from ex


def parse_rsync_log(text_to_parse: str, file_ending_to_cut: str = "") -> RsyncLog:
    """
    Load rsync log produced with formatting "%o %f" as list of recieved files and deleted files. If file ending
    to cut is supplied, only such files are noted and the ending is removed from them.
    :param text_to_parse:
    :param file_ending_to_cut:
    :return: RsyncLog instance.
    :raises ParsingError: In case of file problems or parsing problems.
    """
    unprocessed_lines = []
    rsync_log = RsyncLog()

    for line in text_to_parse.split(os.linesep):
        try:
            operation, filename = line.split(" ")
            if filename == ".":
                continue

            if operation == "del" and file_ending_to_cut in filename:
                rsync_log.deleted.append(filename.replace(file_ending_to_cut, ""))
            elif operation == "recv" and file_ending_to_cut in filename:
                rsync_log.recieved.append(filename.replace(file_ending_to_cut, ""))
            else:
                unprocessed_lines.append(line)
        except ValueError:
            unprocessed_lines.append(line)

    if unprocessed_lines:
        logging.warning(
            "%s lines from rsync log failed to be processed (invalid operation, wrong format or filename did not "
            "contain required file ending). Whole log: %s",
            len(unprocessed_lines),
            text_to_parse
        )
        raise ParsingError(f"{len(unprocessed_lines)} rsync log lines failed to be parsed.")

    return rsync_log
