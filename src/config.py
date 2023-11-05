from dataclasses import dataclass


@dataclass
class Config:
    """
    Class containing configuration for mulsan with default values.
    """
    path_to_ligand_stats_csv: str = "../sample_data/ligandStats.csv"
    logging_debug: bool = True
