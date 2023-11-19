from dataclasses import dataclass
from enum import Enum


# TODO only an idea of how the running of the program could work, subject to changes
class RunModeType(Enum):
    """
    Enum holding the different modes the app can be run in.
    """
    ALL = 0
    DOWNLOAD_ALL = 1
    DOWNLOAD_ARCHIVE_MCIF = 2
    # ...
    TEST = 99


@dataclass
class Config:
    """
    Class containing configuration for mulsan with default values. Switches from commandline will overwrite this.
    """
    # BASIC CONFIG
    logging_debug: bool = False
    # run_mode: RunModeType = RunModeType.ALL
    run_mode: RunModeType = RunModeType.TEST

    # TIMEOUTS
    http_requests_timeout_s: int = 10

    # FILE config
    temporary_files_folder_path: str = "./temp/"
    path_to_ligand_stats_csv: str = "../sample_data/ligandStats.csv"
