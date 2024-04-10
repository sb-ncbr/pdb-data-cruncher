from src.config import Config
from src.generic_file_handlers.simple_lock_handler import (
    check_no_lock_present_preventing_download, create_simple_lock_file, LockType
)


def run_data_download(config: Config) -> bool:
    """
    Download new data and create files with changed pdb ids.
    :param config: Application configuration.
    :return: True if action succeeded. False otherwise.
    """
    check_no_lock_present_preventing_download(config)
    raise NotImplementedError()   # TODO
    create_simple_lock_file(LockType.DATA_EXTRACTION, config)
