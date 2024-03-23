from dataclasses import dataclass, field
from enum import Enum
from os import path


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
    EXTRACT_ALL_INTO_CRUNCHED = 10
    # ...
    CREATE_ALL = 20
    CREATE_DEFAULT_PLOT_DATA = 21
    CREATE_DISTRIBUTION_DATA = 22
    # ...
    TEST = 99


@dataclass(slots=True)
class DefaultPlotSettingsConfig:
    """
    Configuration for creating default plot settings.
    """

    max_bucket_count: int = 50
    min_count_in_bucket: int = 50
    std_outlier_multiplier: int = 2
    allowed_bucket_size_bases: list[int] = field(
        default_factory=lambda: [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90]  # TODO parsing check it's <10, 99>
    )  # TODO and need to be sorted


@dataclass(slots=True)
class FactorHierarchySettings:
    """
    Configuration for updating factor hierarchy.
    """

    min_interval_count: int = 100
    ideal_interval_count: int = 200
    max_interval_count: int = 300
    allowed_slider_size_bases: list[int] = field(
        default_factory=lambda: [10, 20, 25, 50]  # TODO parsing check it's <10, 99> and need to be sorted
    )


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class Config:
    """
    Class containing configuration for mulsan with default values. Switches from commandline will overwrite this.
    """

    # BASIC CONFIG
    logging_debug: bool = False
    # run_mode: RunModeType = RunModeType.ALL
    run_mode: RunModeType = RunModeType.CREATE_ALL

    data_extraction_max_threads: int = 8

    # TIMEOUTS
    http_requests_timeout_s: int = 10

    # SPECIFIC
    default_plot_settings: DefaultPlotSettingsConfig = DefaultPlotSettingsConfig()
    factor_hierarchy_settings: FactorHierarchySettings = FactorHierarchySettings()

    # FILE config TODO defaults with os path join
    path_to_rest_jsons: str = "../dataset/PDBe_REST_API_JSON/"
    path_to_pdbx_files: str = "../dataset/PDBe_updated_mmCIF/"
    path_to_xml_reports: str = "../dataset/ValRep_XML/"
    path_to_validator_db_results: str = "../dataset/MotiveValidator_JSON/"
    path_to_ligand_stats_csv: str = "../dataset/ligandStats.csv"

    crunched_data_csv_path: str = "../crunched_data.csv"

    factor_pairs_autoplot_csv_path: str = path.join(path.pardir, "dataset", "autoplot.csv")
    factor_x_plot_bucket_limits_csv_path: str = path.join(path.pardir, "dataset", "3-Hranice-X_nazvy_promennych.csv")
    familiar_name_translation_path: str = path.join(path.pardir, "dataset", "nametranslation.json")
    factor_hierarchy_path: str = path.join(path.pardir, "dataset", "FactorHierarchy.json")

    versions_path: str = path.join(path.pardir, "dataset", "Versions.json")
    key_treds_versions_path: str = path.join(path.pardir, "dataset", "VersionsKT.json")

    output_files_path: str = path.join(path.pardir, "my_output/")
