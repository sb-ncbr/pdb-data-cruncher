import logging
from os import path
from os import environ as env
from dataclasses import dataclass, field
from typing import Optional

from src.utils import get_formatted_date, int_from_env, bool_from_env, int_list_from_env, get_formatted_timestamp


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
            "DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES", [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90]
        )
    )

    def validate(self) -> None:
        """
        Check values are within allowed limits.
        :raises ValueError:
        """
        if self.max_bucket_count < 10:
            raise ValueError("DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT should be at least 10 for proper results.")

        if len(self.allowed_bucket_base_sizes) == 0:
            raise ValueError("DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES need at least one value.")

        if len(self.allowed_bucket_base_sizes) > 20 or self.max_bucket_count > 100 or self.min_count_in_bucket > 100:
            logging.warning(
                "Given default plot settings may cause the app to run significantly longer. Default plot settings "
                "ideal interval size is determined experimentally - setting allowed base sizes to many options, setting"
                " big max bucket count or large minimal count in bucket may cause it to try more options before finding"
                " a suitable option, and may result in less optimal intervals."
            )

        last_bucket_base_size = None
        for base_size in self.allowed_bucket_base_sizes:
            if not 10 <= base_size < 100:
                raise ValueError("ALLOWED_BUCKET_BASE_SIZES need to be from interval <10,99>")
            if last_bucket_base_size and last_bucket_base_size >= base_size:
                raise ValueError("ALLOWED_BUCKET_BASE_SIZES need to be sorted in the ascending order")
            last_bucket_base_size = base_size


@dataclass(slots=True)
class FactorHierarchyConfig:
    """
    Configuration for updating factor hierarchy.
    """

    min_interval_count: int = int_from_env("FACTOR_HIERARCHY_MIN_INTERVAL_COUNT", 100)
    ideal_interval_count: int = int_from_env("FACTOR_HIERARCHY_IDEAL_INTERVAL_COUNT", 200)
    max_interval_count: int = int_from_env("FACTOR_HIERARCHY_MAX_INTERVAL_COUNT", 300)
    allowed_slider_base_sizes: list[int] = field(
        default_factory=lambda: int_list_from_env("FACTOR_HIERARCHY_ALLOWED_SLIDER_BASE_SIZES", [10, 20, 25, 50])
    )

    def validate(self) -> None:
        """
        Check values are within allowed limits.
        :raises ValueError:
        """
        if self.min_interval_count <= 0:
            raise ValueError("FACTOR_HIERARCHY_MIN_INTERVAL_COUNT needs to be bigger than 0.")

        if self.min_interval_count > self.max_interval_count:
            raise ValueError(
                "FACTOR_HIERARCHY_MIN_INTERVAL_COUNT cannot be bigger than FACTOR_HIERARCHY_MAX_INTERVAL_COUNT."
            )

        if self.ideal_interval_count < self.min_interval_count:
            self.ideal_interval_count = self.min_interval_count
            logging.warning(
                "FACTOR_HIERARCHY_IDEAL_INTERVAL_COUNT was smaller than the FACTOR_HIERARCHY_MIN_INTERVAL_COUNT. "
                "It was set to the minimal value instead."
            )

        if self.ideal_interval_count > self.max_interval_count:
            self.ideal_interval_count = self.max_interval_count
            logging.warning(
                "FACTOR_HIERARCHY_IDEAL_INTERVAL_COUNT was larger than the FACTOR_HIERARCHY_MAX_INTERVAL_COUNT. "
                "It was set to the maximum value instead."
            )

        if len(self.allowed_slider_base_sizes) == 0:
            raise ValueError("FACTOR_HIERARCHY_ALLOWED_SLIDER_BASE_SIZES need at least one value.")

        last_bucket_base_size = None
        for base_size in self.allowed_slider_base_sizes:
            if not 10 <= base_size < 100:
                raise ValueError("FACTOR_HIERARCHY_ALLOWED_SLIDER_BASE_SIZES need to be from interval <10,99>")
            if last_bucket_base_size and last_bucket_base_size >= base_size:
                raise ValueError("FACTOR_HIERARCHY_ALLOWED_SLIDER_BASE_SIZES need to be sorted in the ascending order")
            last_bucket_base_size = base_size


# pylint: disable=missing-function-docstring
@dataclass(slots=True)
class FilepathConfig:
    """
    Configuration
    """

    dataset_root_path: str = env.get("DATASET_ROOT_PATH", "./data/dataset")
    output_root_path: str = env.get("OUTPUT_ROOT_PATH", "./data/output")
    logs_root_path: str = env.get("LOGS_ROOT_PATH", "./data/logs")

    # source of data
    _rest_jsons_name: str = env.get("REST_JSONS_FOLDER_NAME", "PDBe_REST_API_JSON")
    _pdb_mmcifs_name: str = env.get("PDB_MMCIFS_FOLDER_NAME", "PDBe_mmCIF")
    _gzipped_pdb_mmcifs_name: str = env.get("GZIPPED_PDB_MMCIFS_NAME", "gz_PDBe_mmCIF")
    _xml_reports_name: str = env.get("XML_REPORTS_FOLDER_NAME", "ValRep_XML")
    _gzipped_xml_reports_name: str = env.get("GZIPPED_XML_REPORTS_FOLDER_NAME", "gz_ValRep_XML")
    _validator_db_results_name: str = env.get("VALIDATOR_DB_RESULTS_FOLDER_NAME", "MotiveValidator_JSON")
    _ligand_cifs_name: str = env.get("LIGAND_CIFS_FOLDER_NAME", "ccd_CIF")
    _factor_pairs_autoplot_csv_name: str = env.get("AUTOPLOT_CSV_NAME", "autoplot.csv")
    _factor_x_plot_bucket_limits_csv_name: str = env.get(
        "X_PLOT_BUCKET_LIMITS_CSV_NAME", "3-Hranice-X_nazvy_promennych.csv"
    )
    _ligand_occurrence_json_name: str = env.get("LIGAND_OCCURRENCE_JSON_NAME", "ligand_occurrence_in_structures.json")
    _ligand_stats_name: str = env.get("LIGAND_STATS_NAME", "ligandStats.csv")
    _download_changed_ids_json_name: str = env.get(
        "DOWNLOAD_CHANGED_IDS_JSON_NAME", "download_changed_ids_to_update.json"
    )
    _download_failed_ids_to_retry_json_name: str = env.get(
        "DOWNLOAD_FAILED_IDS_TO_RETRY_JSON_NAME", "download_failed_ids_to_retry.json"
    )

    # output names used as input too
    _familiar_name_translations_json_name: str = env.get("FAMILIAR_NAME_TRANSLATIONS_NAME", "nametranslation.json")
    _versions_json_name: str = env.get("VERSIONS_JSON_NAME", "Versions.json")
    _key_trends_versions_json_name: str = env.get("KEY_TRENDS_VERSIONS_JSON_NAME", "VersionsKT.json")
    _old_crunched_csv_name: str = env.get("OLD_CRUNCHED_CSV_NAME", "data.csv")

    # logs
    _full_log_name: str = env.get("FULL_LOG_NAME", "full_log.txt")
    _filtered_log_name: str = env.get("FILTERED_LOG_NAME", "filtered_log.txt")
    _run_start_timesetamp: str = get_formatted_timestamp()

    @property
    def rest_jsons(self) -> str:
        return path.join(self.dataset_root_path, self._rest_jsons_name)

    @property
    def pdb_mmcifs(self) -> str:
        return path.join(self.dataset_root_path, self._pdb_mmcifs_name)

    @property
    def gz_pdb_mmcifs(self) -> str:
        return path.join(self.dataset_root_path, self._gzipped_pdb_mmcifs_name)

    @property
    def xml_reports(self) -> str:
        return path.join(self.dataset_root_path, self._xml_reports_name)

    @property
    def gz_xml_reports(self) -> str:
        return path.join(self.dataset_root_path, self._gzipped_xml_reports_name)

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
    def ligand_occurrence_json(self) -> str:
        return path.join(self.dataset_root_path, self._ligand_occurrence_json_name)

    @property
    def ligand_stats(self) -> str:
        return path.join(self.dataset_root_path, self._ligand_stats_name)

    @property
    def download_changed_ids_json(self) -> str:
        return path.join(self.dataset_root_path, self._download_changed_ids_json_name)

    @property
    def download_failed_ids_to_retry_json(self) -> str:
        return path.join(self.dataset_root_path, self._download_failed_ids_to_retry_json_name)

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
    def old_crunched_csv(self) -> str:
        return path.join(self.output_root_path, self._old_crunched_csv_name)

    @property
    def archive_rsync_logs(self) -> str:
        return path.join(self.logs_root_path, "rsync_log_history")

    @property
    def archive_app_logs(self) -> str:
        return path.join(self.logs_root_path, "full_log_history")

    @property
    def full_log(self) -> str:
        return path.join(self.logs_root_path, self._full_log_name)

    @property
    def filtered_log(self) -> str:
        return path.join(self.logs_root_path, self._filtered_log_name)

    @property
    def archive_full_log(self) -> str:
        return path.join(self.archive_app_logs, f"{self._run_start_timesetamp}_{self._full_log_name}")

    @property
    def mmcif_rsync_log(self) -> str:
        return path.join(self.archive_rsync_logs, f"{self._run_start_timesetamp}_mmcif_rsync_log.txt")

    @property
    def xml_rsync_log(self) -> str:
        return path.join(self.archive_rsync_logs, f"{self._run_start_timesetamp}_xml_rsync_log.txt")


@dataclass(slots=True)
class DownloadTimeoutConfig:
    """
    Configuration for download timeouts.
    """

    rest_timeout_s: int = env.get("DOWNLOAD_REST_TIMEOUT_S", 100)
    ligand_cifs_timeout_s: int = env.get("DOWNLOAD_LIGAND_CIFS_TIMEOUT_S", 30*60)


@dataclass(slots=True)
class Config:
    """
    Application configuraiton.
    """

    logging_debug: bool = bool_from_env("LOGGING_DEBUG", False)
    max_process_count: int = int_from_env("MAX_PROCESS_COUNT", 8)
    current_formatted_date: str = env.get("CURRENT_FORMATTED_DATE", get_formatted_date())

    # data download
    run_data_download_only: bool = bool_from_env("RUN_DATA_DOWNLOAD_ONLY", False)
    override_ids_to_download_filepath: Optional[str] = env.get("OVERRIDE_IDS_TO_DOWNLOAD_PATH")
    skip_data_download: bool = bool_from_env("SKIP_DATA_DOWNLOAD", False)
    # data extraction
    run_data_extraction_only: bool = bool_from_env("RUN_DATA_EXTRACTION_ONLY", False)
    force_complete_data_extraction: bool = bool_from_env("FORCE_COMPLETE_DATA_EXTRACTION", False)
    ids_to_remove_and_update_override_filepath: Optional[str] = env.get("IDS_TO_REMOVE_AND_UPDATE_OVERRIDE_PATH")
    # 7zip data
    run_zipping_files_only: bool = bool_from_env("RUN_ZIPPING_FILES_ONLY", False)
    # data transformation
    run_data_transformation_only: bool = bool_from_env("RUN_DATA_TRANSFORMATION_ONLY", False)
    crunched_csv_name_for_data_transformation_only: str = env.get("CRUNCHED_CSV_NAME_FOR_DATA_TRANSFORMATION", "")
    data_transformation_skip_plot_settings: bool = bool_from_env("DATA_TRANSFORMATION_SKIP_PLOT_SETTINGS", True)
    # post transformation actions
    run_post_transformation_actions_only: bool = bool_from_env("RUN_POST_TRANSFORMATION_ACTIONS_ONLY", False)

    default_plot_settings: DefaultPlotSettingsConfig = field(default_factory=DefaultPlotSettingsConfig)
    factor_hierarchy_settings: FactorHierarchyConfig = field(default_factory=FactorHierarchyConfig)
    filepaths: FilepathConfig = field(default_factory=FilepathConfig)
    timeouts: DownloadTimeoutConfig = field(default_factory=DownloadTimeoutConfig)

    def is_full_run(self) -> bool:
        return (
            not self.run_data_download_only and
            not self.run_data_extraction_only and
            not self.run_zipping_files_only and
            not self.run_data_transformation_only and
            not self.run_post_transformation_actions_only
        )

    def validate(self):
        """
        Check the values set for config are valid for their purpose.
        :raises ValueError:
        """
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
        if self.run_post_transformation_actions_only:
            run_only_mode_count += 1
        if run_only_mode_count > 1:
            raise ValueError(
                "Only one of the options RUN_DATA_DOWNLOAD_ONLY, RUN_DATA_EXTRACTION_ONLY, RUN_ZIPPING_FILES_ONLY, "
                "RUN_DATA_TRANSFORMATION_ONLY, RUN_POST_TRANSFORMATION_ACTIONS_ONLY can be set to True."
            )

        if self.run_data_download_only and self.skip_data_download:
            raise ValueError("Cannot have RUN_DATA_DONWLOAD_ONLY and SKIP_DATA_DOWNLOAD selected at the same time.")

        # transformation settings are valid
        self.factor_hierarchy_settings.validate()
        self.default_plot_settings.validate()

        # max process count is at least 1
        if self.max_process_count < 1:
            raise ValueError("MAX_PROCESS_COUNT needs to be at least 1.")

        # current date is in format 20240101 (has 8 chars that represent digits
        if len(self.current_formatted_date) != 8 or len([c for c in self.current_formatted_date if c.isdigit()]) != 8:
            raise ValueError("CURRENT_FORMATTED_DATE needs to be 8 chars representing digits, e.g. 20240101.")
