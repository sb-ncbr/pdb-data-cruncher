import logging
import os
from enum import Enum

from src.config import Config


class LockType(Enum):
    DATA_EXTRACTION = "data_extraction_lock.txt"
    DATA_ARCHIVATION = "data_archivation_lock.txt"


def create_simple_lock_file(lock_type: LockType, config: Config) -> None:
    filepath = os.path.join(config.filepaths.logs_root_path, lock_type.value)
    with open(filepath, "w", encoding="utf8") as f:
        f.write(
            f"Lock for {lock_type.value} was created after download, but never released. It would have been released "
            f"after successful finish of the {lock_type.value} run. Please check the logs and run this phase standalone"
            " again to ensure the changes from download are propagated. This lock may be removed by simply deleting "
            f"the file, but it is not recommended doing - solve the issue and rerun {lock_type.value} phase instead."
        )
        logging.info(f"Create lock file %s.", filepath)


def release_simple_lock_file(lock_type: LockType, config: Config) -> None:
    filepath = os.path.join(config.filepaths.logs_root_path, lock_type.value)
    if os.path.exists(filepath):
        os.remove(filepath)
        logging.info(f"Deleted (released) lock file %s.", filepath)


def check_no_lock_present_preventing_download(config: Config) -> None:
    """
    Check none of the locks that would prevent download run exist.
    :param config:
    :raises RuntimeError: If such lock actually exists.
    """
    for lock in [LockType.DATA_EXTRACTION, LockType.DATA_ARCHIVATION]:
        filepath = os.path.join(config.filepaths.logs_root_path, lock.value)
        if os.path.exists(filepath):
            raise RuntimeError(
                f"Lock {filepath} for action {lock.value} exists! This means it failed last time and needs to be "
                "rerun standalone first."
            )
