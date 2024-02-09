from dataclasses import dataclass
from enum import Enum


INVALID_VALUE_STRING = "nan"


BIOPOLYMER_MOLECULE_TYPES = [
    "carbohydrate polymer",
    "polypeptide(l)",
    "polypeptide(d)",
    "polyribonucleotide",
    "polydeoxyribonucleotide",
    "polysaccharide(d)",
    "polysaccharide(l)",
    "polydeoxyribonucleotide/polyribonucleotide hybrid",
    "cyclic-pseudo-peptide",
    "peptide nucleic acid",
]
"""
Holds all molecule types that are considered biopolymers for parsing rest molecules.
The comparison ignores upper/lower case differences.
"""


# TODO only an idea of how the running of the program could work, subject to changes
class RunModeType(Enum):
    """
    Enum holding the different modes the app can be run in.
    """

    ALL = 0
    DOWNLOAD_ALL = 1
    DOWNLOAD_ARCHIVE_MMCIF = 2
    # ...
    TEST = 99


@dataclass(frozen=True)
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
    path_to_rest_jsons: str = "./temp/structured/PDBe_REST_API_JSON/"
    path_to_pdb_files: str = "./temp/structured/PDBe_updated_mmCIF/"
    path_to_xml_reports: str = "./temp/structured/ValRep_XML/"
    path_to_validator_db_results: str = "./temp/structured/MotiveValidator_JSON/"
    path_to_ligand_stats_csv: str = "./temp/structured/ligandStats.csv"
