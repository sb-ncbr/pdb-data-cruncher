import logging

from src.config import Config
from src.file_handlers.name_translations_loader import load_familiar_names_translation
from src.file_handlers.autoplot_csv_loader import load_autoplot_factor_pairs
from src.file_handlers.default_plot_data_file_writer import write_default_plot_data_into_zip
from src.data_transformation.default_plot_settings_creator import create_default_plot_settings
from src.data_transformation.default_plot_data_creator import create_default_plot_data
from src.exception import ParsingError, DataTransformationError, FileWritingError


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
        try:
            # load required data
            factor_pairs = load_autoplot_factor_pairs(config.factor_pairs_autoplot_csv_path)
            familiar_names_translation = load_familiar_names_translation(config.familiar_name_translation_path)
            # create default plot data
            default_plot_data_list = create_default_plot_data(
                config.crunched_data_csv_path,
                config.factor_x_plot_bucket_limits_csv_path,
                factor_pairs,
                familiar_names_translation
            )
            # output the plot data
            write_default_plot_data_into_zip(default_plot_data_list, config.output_files_path)
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create default plot data. %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected issue: %s", ex)

    @staticmethod
    def create_default_plot_settings(config: Config) -> None:
        try:
            familiar_names_translation = load_familiar_names_translation(config.familiar_name_translation_path)
            default_plot_settings_list = create_default_plot_settings(
                config.factor_pairs_autoplot_csv_path,
                familiar_names_translation
            )
            # TODO work in progress
            print("This would be put into file:")
            print([item.to_dict() for item in default_plot_settings_list])
            logging.info("Default plot settings created sucefully.")
        except (ParsingError, DataTransformationError) as ex:
            logging.error(ex)
