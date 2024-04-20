import logging
import os
from enum import Enum

from src.config import Config


class LockType(Enum):
    """
    Type of lock and its associated file.
    """

    DATA_EXTRACTION = "data_extraction_lock.txt"


def create_simple_lock_file(lock_type: LockType, logs_folder_path: str) -> None:
    """
    Create simple file associated with given lock type, presence of the file will serve as "lock" for certain actions.
    :param lock_type:
    :param logs_folder_path:
    """
    filepath = os.path.join(logs_folder_path, lock_type.value)
    with open(filepath, "w", encoding="utf8") as f:
        f.write(
            f"Lock for {lock_type.value} was created after download, but never released. It would have been released "
            f"after successful finish of the {lock_type.name} run. Please check the logs and run this phase standalone"
            " again to ensure the changes from download are propagated. This lock may be removed by simply deleting "
            f"the file, but it is not recommended doing - solve the issue and rerun {lock_type.value} phase instead."
        )
        logging.info("Create lock file %s.", filepath)


def release_simple_lock_file(lock_type: LockType, config: Config) -> None:
    """
    Delete simple file associataed with given lock type, effectively releasing it.
    :param lock_type:
    :param config:
    """
    filepath = os.path.join(config.filepaths.logs_root_path, lock_type.value)
    if os.path.exists(filepath):
        os.remove(filepath)
        logging.info("Deleted (released) lock file %s.", filepath)


def check_no_lock_present_preventing_download(config: Config) -> None:
    """
    Check none of the locks that would prevent download run exist.
    :param config:
    :raises RuntimeError: If such lock actually exists.
    """
    for lock in [LockType.DATA_EXTRACTION]:
        filepath = os.path.join(config.filepaths.logs_root_path, lock.value)
        if os.path.exists(filepath):
            raise RuntimeError(
                f"Lock {filepath} for action {lock.name} exists! This means it failed last time and needs to be "
                "rerun standalone first."
            )
