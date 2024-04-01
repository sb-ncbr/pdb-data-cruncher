import logging
from dataclasses import dataclass, field

from src.exception import ParsingError
from src.generic_file_handlers.plain_text_loader import load_text_file_as_lines


@dataclass(slots=True)
class RsyncLog:
    recieved: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


def load_rsync_log(filepath: str, file_ending_to_cut: str = "") -> RsyncLog:
    """
    Load rsync log produced with formatting "%o %f" as list of recieved files and deleted files. If file ending
    to cut is supplied, only such files are noted and the ending is removed from them.
    :param filepath:
    :param file_ending_to_cut:
    :return: RsyncLog instance.
    :raises ParsingError: In case of file problems or parsing problems.
    """
    unprocessed_lines = []
    rsync_log = RsyncLog()

    for line in load_text_file_as_lines(filepath):
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
            "%s lines from rsync log %s failed to be processed (invalid operation, wrong format or filename did not "
            "contain required file ending). The failed lines: %s.",
            len(unprocessed_lines),
            filepath,
            unprocessed_lines
        )
        raise ParsingError(f"{len(unprocessed_lines)} rsync log lines failed to load from {filepath}.")

    return rsync_log
