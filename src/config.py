from os import path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils import get_formatted_date


# TODO remove later
class RunModeType(Enum):
    """
    Enum holding the different modes the app can be run in.
    """

    ALL = 0
    DOWNLOAD_ONLY = 1
    EXTRACT_INTO_CRUNCHED_ONLY = 2
    TRANSFORM_ONLY = 3
    ZIP_ONLY = 4

    DOWNLOAD_ALL = 1
    DOWNLOAD_ARCHIVE_MMCIF = 2
    # ...
    EXTRACT_ALL_INTO_CRUNCHED = 10
    # ...
    CREATE_ALL = 20
    CREATE_DEFAULT_PLOT_DATA = 21
    CREATE_DISTRIBUTION_DATA = 22
    CREATE_DEFAULT_PLOT_SETTINGS = 23
    CREATE_FACTOR_HIERARCHY = 24
    CREATE_VERSION_JSONS = 25
    CREATE_COPIES_OF_MINOR_FILES = 26
    CREATE_7Z_ARCHIVES = 27


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
    resume_previous_run: bool = True
    max_process_count_in_multiprocessing: int = 8
    # TIMEOUTS
    http_requests_timeout_s: int = 10
    # SPECIFIC
    default_plot_settings: DefaultPlotSettingsConfig = DefaultPlotSettingsConfig()
    factor_hierarchy_settings: FactorHierarchySettings = FactorHierarchySettings()

    # FILE config
    raw_dataset_root_path: str = "../raw_dataset/"
    output_root_path: str = "../output/"

    path_to_rest_jsons: str = path.join(raw_dataset_root_path, "PDBe_REST_API_JSON/")
    path_to_pdbx_files: str = path.join(raw_dataset_root_path, "PDBe_updated_mmCIF/")
    path_to_xml_reports: str = path.join(raw_dataset_root_path, "ValRep_XML/")
    path_to_validator_db_results: str = path.join(raw_dataset_root_path, "MotiveValidator_JSON/")
    factor_pairs_autoplot_csv_path: str = path.join(output_root_path, "autoplot.csv")
    factor_x_plot_bucket_limits_csv_path: str = path.join(raw_dataset_root_path, "3-Hranice-X_nazvy_promennych.csv")
    path_to_ligand_stats_csv: str = path.join(raw_dataset_root_path, "ligandStats.csv")

    familiar_name_translation_path: str = path.join(output_root_path, "nametranslation.json")
    factor_hierarchy_path: str = path.join(output_root_path, "FactorHierarchy.json")
    versions_path: str = path.join(output_root_path, "Versions.json")
    key_treds_versions_path: str = path.join(output_root_path, "VersionsKT.json")

    run_mode: RunModeType = RunModeType.CREATE_ALL
    crunched_data_csv_path: str = path.join(output_root_path, f"{get_formatted_date()}_crunched.csv")


@dataclass(slots=True)
class FilepathConfig:
    dataset_root_path: str = "../raw_dataset/"  # TODO not the final value
    output_root_path: str = "../output/"  # TODO not the final value
    log_root_path: str = "../logs/"  # TODO not the final value

    # source of data
    _rest_jsons_name: str = "PDBe_REST_API_JSON"
    _pdb_mmcifs_name: str = "PDBe_updated_mmCIF"
    _xml_reports_name: str = "ValRep_XML"
    _validator_db_results_name: str = "MotiveValidator_JSON"
    _ligand_cifs_name: str = "ccd_CIF"
    _factor_pairs_autoplot_csv_name: str = "autoplot.csv"
    _factor_x_plot_bucket_limits_csv_name: str = "3-Hranice-X_nazvy_promennych.csv"
    _ligand_occurence_json_name: str = "ligand_occurence_in_pdb_ids.json"

    # output names used as input too
    _familiar_name_translations_json_name: str = "nametranslation.json"
    _factor_hierarchy_json_name: str = "FactorHierarchy.json"
    _versions_json_name: str = "Versions.json"
    _key_trends_versions_json_name: str = "VersionsKT.json"
    _ligand_stats_name: str = "ligandStats.csv"

    # logs
    _full_log_name: str = "full_log.txt"
    _warning_and_error_log_name: str = "warning_and_error_log.txt"
    # TODO somehow include updated pdb mmcifs log file
    # TODO somehow include updated ligands log file

    @property
    def rest_jsons(self) -> str:
        return path.join(self.dataset_root_path, self._rest_jsons_name)

    @property
    def pdb_mmcifs(self) -> str:
        return path.join(self.dataset_root_path, self._pdb_mmcifs_name)

    @property
    def xml_reports(self) -> str:
        return path.join(self.dataset_root_path, self._xml_reports_name)

    @property
    def validator_db_results(self) -> str:
        return path.join(self.dataset_root_path, self._validator_db_results_name)

    @property
    def ligand_cifs(self) -> str:
        return path.join(self.dataset_root_path, self._ligand_cifs_name)

    @property
    def factor_pairs_autoplot_csv(self) -> str:
        return path.join(self.dataset_root_path, self._factor_pairs_autoplot_csv_name)

    @property
    def factor_x_plot_bucket_limits_csv(self) -> str:
        return path.join(self.dataset_root_path, self._factor_x_plot_bucket_limits_csv_name)

    @property
    def ligand_occurence_json(self) -> str:
        return path.join(self.dataset_root_path, self._ligand_occurence_json_name)

    @property
    def familiar_name_translations_json(self) -> str:
        return path.join(self.output_root_path, self._familiar_name_translations_json_name)

    @property
    def factor_hierarchy_json(self) -> str:
        return path.join(self.output_root_path, self._factor_hierarchy_json_name)

    @property
    def versions_json(self) -> str:
        return path.join(self.output_root_path, self._versions_json_name)

    @property
    def key_trends_versions_json(self) -> str:
        return path.join(self.output_root_path, self._key_trends_versions_json_name)

    @property
    def ligand_stats(self) -> str:
        return path.join(self.output_root_path, self._ligand_stats_name)

    @property
    def full_log(self) -> str:
        return path.join(self.log_root_path, self._full_log_name)

    @property
    def warning_and_error_log(self) -> str:
        return path.join(self.log_root_path, self._warning_and_error_log_name)


@dataclass(slots=True)
class NewConfig:
    logging_debug: bool = False
    max_process_count: int = 8

    # data download
    run_data_download_only: bool = False
    # data extraction
    run_data_extraction_only: bool = False
    force_complete_data_extraction: bool = False
    pdb_ids_to_update: Optional[list[str]] = None
    # 7zip data
    run_zipping_files_only: bool = False
    force_complete_7zip_integrity_check: bool = False
    # data transformation
    run_data_transformation_only: bool = False
    crunched_csv_path_for_data_transformation_only: str = ""
    data_transformation_skip_plot_settings: bool = True
    default_plot_settings: DefaultPlotSettingsConfig = DefaultPlotSettingsConfig()
    factor_hierarchy_settings: FactorHierarchySettings = FactorHierarchySettings()

    filepaths: FilepathConfig = FilepathConfig()

