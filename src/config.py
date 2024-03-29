from os import path
from os import environ as env
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils import get_formatted_date, int_from_env, bool_from_env, int_list_from_env, string_list_from_env


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

    max_bucket_count: int = int_from_env("DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT", 50)
    min_count_in_bucket: int = int_from_env("DEFAULT_PLOT_SETTINGS_MIN_BUCKET_COUNT", 50)
    std_outlier_multiplier: int = int_from_env("DEFAULT_PLOT_SETTINGS_STD_OUTLIER_MULTIPLIER", 2)
    allowed_bucket_base_sizes: list[int] = field(
        default_factory=lambda: int_list_from_env(
            "ALLOWED_BUCKET_BASE_SIZES", [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90]
        )
    )

    def validate(self) -> None:
        if len(self.allowed_bucket_base_sizes) == 0:
            raise ValueError("ALLOWED_BUCKET_BASE_SIZES need at least one value.")

        last_bucket_base_size = None
        for base_size in self.allowed_bucket_base_sizes:
            if not 10 <= base_size <= 100:
                raise ValueError("ALLOWED_BUCKET_BASE_SIZES need to be from interval <10,99>")
            if last_bucket_base_size and last_bucket_base_size >= base_size:
                raise ValueError("ALLOWED_BUCKET_BASE_SIZES need to be sorted in the ascending order")
            last_bucket_base_size = base_size


@dataclass(slots=True)
class FactorHierarchySettings:
    """
    Configuration for updating factor hierarchy.
    """

    min_interval_count: int = int_from_env("FACTOR_HIERARCHY_MIN_INTERVAL_COUNT", 100)
    ideal_interval_count: int = int_from_env("FACTOR_HIERARCHY_IDEAL_INTERVAL_COUNT", 200)
    max_interval_count: int = int_from_env("FACTOR_HIERARCHY_MAX_INTERVAL_COUNT", 300)
    allowed_slider_base_sizes: list[int] = field(
        default_factory=lambda: int_list_from_env("ALLOWED_SLIDER_BASE_SIZES", [10, 20, 25, 50])
    )

    def validate(self) -> None:
        if len(self.allowed_slider_base_sizes) == 0:
            raise ValueError("ALLOWED_SLIDER_BASE_SIZES need at least one value.")

        last_bucket_base_size = None
        for base_size in self.allowed_slider_base_sizes:
            if not 10 <= base_size <= 100:
                raise ValueError("ALLOWED_SLIDER_BASE_SIZES need to be from interval <10,99>")
            if last_bucket_base_size and last_bucket_base_size >= base_size:
                raise ValueError("ALLOWED_SLIDER_BASE_SIZES need to be sorted in the ascending order")
            last_bucket_base_size = base_size


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


# pylint: disable=missing-function-docstring
@dataclass(slots=True)
class FilepathConfig:
    """
    Configuration
    """
    dataset_root_path: str = env.get("DATASET_ROOT_PATH", path.join("app", "dataset"))
    output_root_path: str = env.get("OUTPUT_ROOT_PATH", path.join("app", "output"))
    logs_root_path: str = env.get("LOGS_ROOT_PATH", path.join("app", "logs"))

    # source of data
    _rest_jsons_name: str = env.get("REST_JSONS_FOLDER_NAME", "PDBe_REST_API_JSON")
    _pdb_mmcifs_name: str = env.get("PDB_MMCIFS_FOLDER_NAME", "PDBe_updated_mmCIF")
    _xml_reports_name: str = env.get("XML_REPORTS_FOLDER_NAME", "ValRep_XML")
    _validator_db_results_name: str = env.get("VALIDATOR_DB_RESULTS_FOLDER_NAME", "MotiveValidator_JSON")
    _ligand_cifs_name: str = env.get("LIGAND_CIFS_FOLDER_NAME", "ccd_CIF")
    _factor_pairs_autoplot_csv_name: str = env.get("AUTOPLOT_CSV_NAME", "autoplot.csv")
    _factor_x_plot_bucket_limits_csv_name: str = env.get(
        "X_PLOT_BUCKET_LIMITS_CSV_NAME", "3-Hranice-X_nazvy_promennych.csv"
    )
    _ligand_occurrence_json_name: str = env.get("LIGAND_OCCURRENCE_JSON_NAME", "ligand_occurence_in_pdb_ids.json")

    # output names used as input too
    _familiar_name_translations_json_name: str = env.get("FAMILIAR_NAME_TRANSLATIONS_NAME", "nametranslation.json")
    _versions_json_name: str = env.get("VERSIONS_JSON_NAME", "Versions.json")
    _key_trends_versions_json_name: str = env.get("KEY_TRENDS_VERSIONS_JSON_NAME", "VersionsKT.json")
    _ligand_stats_name: str = env.get("LIGAND_STATS_NAME", "ligandStats.csv")

    # logs
    _full_log_name: str = env.get("FULL_LOG_NAME", "full_log.txt")
    _previous_full_log_name: str = env.get("PREVIOUS_FULL_LOG_NAME", "previous_full_log.txt")
    _filtered_log_name: str = env.get("FILTERED_LOG_NAME", "filtered_log.txt")
    _previous_filtered_log_name: str = env.get("PREVIOUS_FILTERED_LOG_NAME", "previous_filtered_log.txt")
    # TODO somehow include updated pdb mmcifs log file, ideally with previous version like logs
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
        return path.join(self.dataset_root_path, self._ligand_occurrence_json_name)

    @property
    def familiar_name_translations_json(self) -> str:
        return path.join(self.output_root_path, self._familiar_name_translations_json_name)

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
        return path.join(self.logs_root_path, self._full_log_name)

    @property
    def previous_full_log(self) -> str:
        return path.join(self.logs_root_path, self._previous_full_log_name)

    @property
    def filtered_log(self) -> str:
        return path.join(self.logs_root_path, self._filtered_log_name)

    @property
    def previous_filtered_log(self) -> str:
        return path.join(self.logs_root_path, self._previous_filtered_log_name)


@dataclass(slots=True)
class NewConfig:
    """
    Application configuraiton.
    """

    logging_debug: bool = bool_from_env("LOGGING_DEBUG", False)
    max_process_count: int = int_from_env("MAX_PROCESS_COUNT", 8)
    current_formatted_date: str = env.get("CURRENT_FORMATTED_DATE", get_formatted_date())
    # TODO use this everywhere instead of get_formatted_date

    # data download
    run_data_download_only: bool = bool_from_env("RUN_DATA_DOWNLOAD_ONLY", False)
    # data extraction
    run_data_extraction_only: bool = bool_from_env("RUN_DATA_EXTRACTION_ONLY", False)
    force_complete_data_extraction: bool = bool_from_env("FORCE_COMPLETE_DATA_EXTRACTION", False)
    pdb_ids_to_update: Optional[list[str]] = field(
        default_factory=lambda: string_list_from_env("PDB_IDS_TO_UPDATE")
    )
    pdb_ids_to_update_filepath: Optional[str] = env.get("PDB_IDS_TO_UPDATE_FILEPATH")
    # 7zip data
    run_zipping_files_only: bool = bool_from_env("RUN_ZIPPING_FILES_ONLY", False)
    force_7zip_integrity_check: bool = bool_from_env("FORCE_7ZIP_INTEGRITY_CHECK", False)
    # data transformation
    run_data_transformation_only: bool = bool_from_env("RUN_DATA_TRANSFORMATION_ONLY", False)
    crunched_csv_name_for_data_transformation_only: str = env.get("CRUNCHED_CSV_NAME_FOR_DATA_TRANSFORMATION", "")
    data_transformation_skip_plot_settings: bool = bool_from_env("DATA_TRANSFORMATION_SKIP_PLOT_SETTINGS", True)

    default_plot_settings: DefaultPlotSettingsConfig = DefaultPlotSettingsConfig()
    factor_hierarchy_settings: FactorHierarchySettings = FactorHierarchySettings()
    filepaths: FilepathConfig = FilepathConfig()

    def validate(self):
        # at most 1 standalone mode is set
        run_only_mode_count = 0
        if self.run_data_download_only:
            run_only_mode_count += 1
        if self.run_data_extraction_only:
            run_only_mode_count += 1
        if self.run_zipping_files_only:
            run_only_mode_count += 1
        if self.run_data_transformation_only:
            run_only_mode_count += 1
        if run_only_mode_count > 1:
            raise ValueError(
                "Only one of the options RUN_DATA_DOWNLOAD_ONLY, RUN_DATA_EXTRACTION_ONLY, RUN_ZIPPING_FILES_ONLY, "
                "RUN_DATA_TRANSFORMATION_ONLY can be set to True."
            )

        # if extraction only wihtout force complete run, pdb ids are passed
        if self.run_data_extraction_only and not self.force_complete_data_extraction:
            pdb_ids_sources = 0
            if self.pdb_ids_to_update_filepath:
                pdb_ids_sources += 1
            if self.pdb_ids_to_update:
                pdb_ids_sources += 1
            if pdb_ids_sources != 1:
                raise ValueError(
                    f"Found {pdb_ids_sources} sources for PDB IDS to run. When data extraction is run standalone, "
                    "exactly one source for pdb ids to run needs to be passed: either PDB_IDS_TO_UPDATE as comma "
                    "separated list, or PDB_IDS_TO_UPDATE_FILEPATH with list of pdb ids."
                )

        # transformation settings are valid
        self.factor_hierarchy_settings.validate()
        self.default_plot_settings.validate()

        # max process count is at least 1
        if self.max_process_count < 1:
            raise ValueError("MAX_PROCESS_COUNT needs to be at least 1.")

        # current date is in format 20240101 (has 8 chars that represent digits
        if len(self.current_formatted_date) != 8 or len([c for c in self.current_formatted_date if c.isdigit()]) != 8:
            raise ValueError("CURRENT_FORMATTED_DATE needs to be 8 chars representing digits, e.g. 20240101.")
