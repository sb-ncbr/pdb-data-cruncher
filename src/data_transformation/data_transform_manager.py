import logging

from src.config import Config
from src.data_transformation.default_plot_data_creator import create_default_plot_data
from src.data_transformation.distribution_data_creator import create_distribution_data
from src.data_transformation.default_plot_settings_creator import create_default_plot_settings
from src.exception import ParsingError, DataTransformationError, FileWritingError
from src.file_handlers.csv_reader import load_csv_as_dataframe
from src.file_handlers.autoplot_csv_loader import load_autoplot_factor_pairs
from src.file_handlers.default_plot_data_file_writer import create_default_plot_data_files
from src.file_handlers.distribution_data_file_writer import create_distribution_data_files
from src.file_handlers.default_plot_settings_file_writer import create_default_plot_settings_file
from src.file_handlers.name_translations_loader import (
    load_factor_names_translations, load_factor_type_names_translations
)


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
            # create default plot settings
            default_plot_setting_list = create_default_plot_settings(crunched_df, factor_types_with_translations)
            # save default plot setting into file
            create_default_plot_settings_file(default_plot_setting_list, config.output_files_path)
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create default plot settings. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
