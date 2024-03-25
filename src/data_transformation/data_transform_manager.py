import logging

from src.config import Config
from src.data_transformation.default_plot_data_creator import create_default_plot_data
from src.data_transformation.distribution_data_creator import create_distribution_data
from src.data_transformation.default_plot_settings_creator import create_default_plot_settings
from src.data_transformation.factor_hierarchy_updater import update_factor_hierarchy
from src.data_transformation.versions_updater import update_versions_json
from src.exception import ParsingError, DataTransformationError, FileWritingError
from src.file_handlers.csv_reader import load_csv_as_dataframe
from src.file_handlers.autoplot_csv_loader import load_autoplot_factor_pairs
from src.file_handlers.json_file_loader import load_json_file
from src.file_handlers.default_plot_data_file_writer import create_default_plot_data_files
from src.file_handlers.distribution_data_file_writer import create_distribution_data_files
from src.file_handlers.default_plot_settings_file_writer import create_default_plot_settings_file
from src.file_handlers.versions_file_writer import create_versions_file, VersionsType
from src.file_handlers.name_translations_loader import (
    load_factor_names_translations,
    load_factor_type_names_translations,
)
from src.file_handlers.file_copier import copy_file_to_output_files
from src.file_handlers.factor_hierarchy_file_writer import create_factor_hierarchy_file
from src.file_handlers.seven_zip_archive_creator import create_archive_of_folder
from src.utils import get_formatted_date


class DataTransformManager:
    """
    Class with only static methods aggregating functions around creating new files out of crunched data
    for the valtrends db backend.
    """

    @staticmethod
    def create_default_plot_data(config: Config) -> None:
        """
        Create all default plot data for each factor pair from autoplot. Creates them as jsons into zip archive.
        :param config: App configuration.
        """
        logging.info("Starting the creation of default plot data output files.")
        try:
            # load required data
            factor_pairs = load_autoplot_factor_pairs(config.factor_pairs_autoplot_csv_path)
            familiar_names_translation = load_factor_names_translations(config.familiar_name_translation_path)
            crunched_df = load_csv_as_dataframe(config.crunched_data_csv_path)
            x_factor_bucket_limits_df = load_csv_as_dataframe(config.factor_x_plot_bucket_limits_csv_path)
            # create default plot data
            default_plot_data_list = create_default_plot_data(
                crunched_df,
                x_factor_bucket_limits_df,
                factor_pairs,
                familiar_names_translation,
            )
            # output the plot data
            create_default_plot_data_files(default_plot_data_list, config.output_files_path)
            logging.info("Creation of default plot data finished successfully.")
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create default plot data. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)

    @staticmethod
    def create_distribution_data(config: Config) -> None:
        """
        Create all default plot data for each factor from names translations. Creates them as jsons into zip archive.
        :param config: App configuration.
        """
        logging.info("Starting the creation of distribution data output files.")
        try:
            # load required data
            factor_types_with_translations = load_factor_type_names_translations(config.familiar_name_translation_path)
            crunched_df = load_csv_as_dataframe(config.crunched_data_csv_path)
            # create distribution data
            distribution_data_list = create_distribution_data(
                crunched_df, list(factor_types_with_translations.keys()), factor_types_with_translations
            )
            # save distribution data into files
            create_distribution_data_files(distribution_data_list, config.output_files_path)
            logging.info("Creation of distribution data finished successfully.")
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create distribution data. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)

    @staticmethod
    def create_default_plot_settings(config: Config) -> None:
        """
        Create default plot settings json with plot settings for each factor.
        :param config: App configuration.
        """
        logging.info("Starting the creation of default plot settings.")
        try:
            # load required data
            factor_types_with_translations = load_factor_type_names_translations(config.familiar_name_translation_path)
            crunched_df = load_csv_as_dataframe(config.crunched_data_csv_path)
            factor_hierarchy_json = load_json_file(config.factor_hierarchy_path)
            # create default plot settings
            default_plot_setting_list = create_default_plot_settings(
                crunched_df, factor_types_with_translations, factor_hierarchy_json, config.default_plot_settings
            )
            # save default plot setting into file
            create_default_plot_settings_file(default_plot_setting_list, config.output_files_path)
            logging.info("Creation of default plot settings finished successfully.")
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create default plot settings. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)

    @staticmethod
    def create_updated_factor_hierarchy(config: Config) -> None:
        """
        Create updated version of factor hierarchy json.
        :param config: App configuration.
        """
        logging.info("Starting the update of factor hierarchy json.")
        try:
            # load required data
            factor_hierarchy_json = load_json_file(config.factor_hierarchy_path)
            crunched_df = load_csv_as_dataframe(config.crunched_data_csv_path)
            factor_types_with_translations = load_factor_type_names_translations(config.familiar_name_translation_path)
            # create updated factor hierarchy json
            update_factor_hierarchy(
                factor_hierarchy_json, crunched_df, factor_types_with_translations, config.factor_hierarchy_settings
            )
            # save the updated factor hierarchy json
            create_factor_hierarchy_file(factor_hierarchy_json, config.output_files_path)
            logging.info("Update of factor hierarchy finished successfully.")
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to update factor hierarchy. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)

    @staticmethod
    def create_updated_versions_jsons(config: Config) -> None:
        """
        Create updated versions json and versionsKT json.
        :param config: App configuration.
        """
        logging.info("Starting the update of version jsons.")
        try:
            # load required data
            versions_json = load_json_file(config.versions_path)
            key_trends_versions_json = load_json_file(config.key_treds_versions_path)
            # update the data
            update_versions_json(versions_json)
            update_versions_json(key_trends_versions_json)
            # save the data into new files
            create_versions_file(versions_json, VersionsType.VERSIONS, config.output_files_path)
            create_versions_file(key_trends_versions_json, VersionsType.KEY_TRENDS_VERSIONS, config.output_files_path)
            logging.info("Update of versions jsons finished successfully.")
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to update version jsons. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)

    @staticmethod
    def copy_name_translations(config: Config) -> None:
        """
        Copy name translations as two files on the output.
        :param config: App configuration.
        """
        logging.info("Starting the copying of name translations files.")
        try:
            copy_file_to_output_files(
                config.familiar_name_translation_path,
                config.output_files_path,
                f"{get_formatted_date()}_NameTranslation.json",
            )
            copy_file_to_output_files(
                config.familiar_name_translation_path,
                config.output_files_path,
                "nametranslation.json",
            )
            logging.info("Name translation files copying finished successfully.")
        except FileWritingError as ex:
            logging.error("Failed to copy name translation files. %s", ex)

    @staticmethod
    def copy_spearman_coefficient_tables(config: Config) -> None:
        """
        Copy two spearman coefficient tables (pdf and xlsx) to output.
        :param config: App configuration.
        """
        logging.info("Starting the copying of spearman coefficient tables.")
        try:
            copy_file_to_output_files(
                config.spearman_coefficient_table_xslx_path,
                config.output_files_path,
                "table.xlsx",
            )
            copy_file_to_output_files(
                config.spearman_coefficient_table_pdf_path,
                config.output_files_path,
                "table.pdf",
            )
            logging.info("Copying spearman coefficient tables finished successfully.")
        except FileWritingError as ex:
            logging.error("Failed to copy spearman coefficent tables. %s", ex)

    @staticmethod
    def create_7z_data_files(config: Config) -> None:
        logging.info("Starting creation of 7z archives.")
        create_archive_of_folder(config.path_to_pdbx_files, config.output_files_path, "rawpdbe.7z")
        create_archive_of_folder(config.path_to_xml_reports, config.output_files_path, "rawvalidxml.7z")
        create_archive_of_folder(config.path_to_rest_jsons, config.output_files_path, "rawrest.7z")
        create_archive_of_folder(config.path_to_validator_db_results, config.output_files_path, "rawvdb.7z")
        logging.info("Creation of 7z archives finished successfully.")
