import logging
from os import path

from src.config import Config
from src.data_transformation.default_plot_data_creator import create_default_plot_data
from src.data_transformation.default_plot_settings_creator import create_default_plot_settings
from src.data_transformation.distribution_data_creator import create_distribution_data
from src.data_transformation.factor_hierarchy_updater import update_factor_hierarchy
from src.data_transformation.file_handlers.autoplot_csv_loader import load_autoplot_factor_pairs
from src.data_transformation.file_handlers.default_plot_data_file_writer import (
    create_default_plot_data_files,
    delete_old_default_plot_data_files,
)
from src.data_transformation.file_handlers.default_plot_settings_file_writer import (
    create_default_plot_settings_file,
    delete_old_default_plot_settings_files,
    rename_default_plot_settings_to_current_date,
)
from src.data_transformation.file_handlers.distribution_data_file_writer import (
    create_distribution_data_files,
    delete_old_distribution_data_files,
)
from src.data_transformation.file_handlers.factor_hierarchy_file_writer import (
    create_factor_hierarchy_file,
    find_older_factor_hierarchy_file,
    delete_old_factor_hierarchy_files,
)
from src.data_transformation.file_handlers.name_translations_loader import (
    load_factor_names_translations,
    load_factor_type_names_translations,
)
from src.data_transformation.versions_updater import update_versions_json
from src.exception import ParsingError, DataTransformationError, FileWritingError
from src.generic_file_handlers.csv_handler import load_csv_as_dataframe
from src.generic_file_handlers.json_file_loader import load_json_file
from src.generic_file_handlers.json_file_writer import write_json_file


class DataTransformManager:
    """
    Class with only static methods aggregating functions around creating new files out of crunched data
    for the valtrends db backend.
    """

    @staticmethod
    def create_default_plot_data(config: Config, crunched_csv_path: str) -> bool:
        """
        Create all default plot data for each factor pair from autoplot. Creates them as jsons into zip archive.
        :param config: App configuration.
        :param crunched_csv_path:
        :returns: True if suceeded.
        """
        logging.info("Starting the creation of default plot data output files.")
        try:
            # load required data
            factor_pairs = load_autoplot_factor_pairs(config.filepaths.factor_pairs_autoplot_csv)
            familiar_names_translation = load_factor_names_translations(
                config.filepaths.familiar_name_translations_json
            )
            crunched_df = load_csv_as_dataframe(crunched_csv_path)
            x_factor_bucket_limits_df = load_csv_as_dataframe(config.filepaths.factor_x_plot_bucket_limits_csv)
            # create default plot data
            default_plot_data_list = create_default_plot_data(
                crunched_df,
                x_factor_bucket_limits_df,
                factor_pairs,
                familiar_names_translation,
            )
            # output the plot data
            create_default_plot_data_files(
                default_plot_data_list, config.filepaths.output_root_path, config.current_formatted_date
            )
            delete_old_default_plot_data_files(config.filepaths.output_root_path, config.current_formatted_date)
            logging.info("Creation of default plot data finished successfully.")
            return True
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create default plot data. %s", ex)
            return False
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
            return False

    @staticmethod
    def create_distribution_data(config: Config, crunched_csv_path: str) -> bool:
        """
        Create all default plot data for each factor from names translations. Creates them as jsons into zip archive.
        :param config: App configuration.
        :param crunched_csv_path:
        :returns: True if suceeded.
        """
        logging.info("Starting the creation of distribution data output files.")
        try:
            # load required data
            factor_types_with_translations = load_factor_type_names_translations(
                config.filepaths.familiar_name_translations_json
            )
            crunched_df = load_csv_as_dataframe(crunched_csv_path)
            # create distribution data
            distribution_data_list = create_distribution_data(
                crunched_df, list(factor_types_with_translations.keys()), factor_types_with_translations
            )
            # save distribution data into files
            create_distribution_data_files(
                distribution_data_list, config.filepaths.output_root_path, config.current_formatted_date
            )
            delete_old_distribution_data_files(config.filepaths.output_root_path, config.current_formatted_date)
            logging.info("Creation of distribution data finished successfully.")
            return True
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create distribution data. %s", ex)
            return False
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
            return False

    @staticmethod
    def create_default_plot_settings(config: Config, crunched_csv_path: str, factor_hierarchy_path: str) -> bool:
        """
        Create default plot settings json with plot settings for each factor.
        :param config: App configuration.
        :param crunched_csv_path:
        :param factor_hierarchy_path: Path to factor hierarchy json.
        :returns: True if suceeded.
        """
        logging.info("Starting the creation of default plot settings.")
        try:
            # load required data
            factor_types_with_translations = load_factor_type_names_translations(
                config.filepaths.familiar_name_translations_json
            )
            crunched_df = load_csv_as_dataframe(crunched_csv_path)
            factor_hierarchy_json = load_json_file(factor_hierarchy_path)
            # create default plot settings
            default_plot_setting_list = create_default_plot_settings(
                crunched_df, factor_types_with_translations, factor_hierarchy_json, config.default_plot_settings
            )
            # save default plot setting into file
            create_default_plot_settings_file(
                default_plot_setting_list, config.filepaths.output_root_path, config.current_formatted_date
            )
            delete_old_default_plot_settings_files(config.filepaths.output_root_path, config.current_formatted_date)
            logging.info("Creation of default plot settings finished successfully.")
            return True
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to create default plot settings. %s", ex)
            return False
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
            return False

    @staticmethod
    def copy_default_plot_settings(config: Config) -> bool:
        """
        For skipping the default plot settings creation, this function only copies the first old file following
        the default plot settings naming scheme it finds.
        :param config: App configuration.
        """
        logging.info("Starting the copying of default plot settings.")
        try:
            rename_default_plot_settings_to_current_date(
                config.filepaths.output_root_path, config.current_formatted_date
            )
            delete_old_default_plot_settings_files(config.filepaths.output_root_path, config.current_formatted_date)
            logging.info("Copying of defualt plot settings finished successfully.")
            return True
        except DataTransformationError as ex:
            logging.error("Failed to copy default plot settings. %s", ex)
            return False
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
            return False

    @staticmethod
    def create_updated_factor_hierarchy(config: Config, crunched_csv_path: str, factor_hierarchy_path: str) -> bool:
        """
        Create updated version of factor hierarchy json.
        :param config: App configuration.
        :param crunched_csv_path:
        :returns: True if suceeded.
        """
        logging.info("Starting the update of factor hierarchy json.")
        try:
            # load required data
            factor_hierarchy_json = load_json_file(factor_hierarchy_path)
            crunched_df = load_csv_as_dataframe(crunched_csv_path)
            factor_types_with_translations = load_factor_type_names_translations(
                config.filepaths.familiar_name_translations_json
            )
            # create updated factor hierarchy json
            update_factor_hierarchy(
                factor_hierarchy_json, crunched_df, factor_types_with_translations, config.factor_hierarchy_settings
            )
            # save the updated factor hierarchy json
            create_factor_hierarchy_file(
                factor_hierarchy_json, config.filepaths.output_root_path, config.current_formatted_date
            )
            delete_old_factor_hierarchy_files(config.filepaths.output_root_path, config.current_formatted_date)
            logging.info("Update of factor hierarchy finished successfully.")
            return True
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to update factor hierarchy. %s", ex)
            return False
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
            return False

    @staticmethod
    def create_updated_versions_jsons(config: Config) -> bool:
        """
        Create updated versions json and versionsKT json.
        :param config: App configuration.
        :returns: True if suceeded.
        """
        logging.info("Starting the update of version jsons.")
        try:
            # load required data
            versions_json = load_json_file(config.filepaths.versions_json)
            key_trends_versions_json = load_json_file(config.filepaths.key_trends_versions_json)
            # update the data
            update_versions_json(versions_json, config.current_formatted_date)
            update_versions_json(key_trends_versions_json, config.current_formatted_date)
            # save the data into new files
            write_json_file(config.filepaths.versions_json, versions_json)
            write_json_file(config.filepaths.key_trends_versions_json, key_trends_versions_json)
            logging.info("Update of versions jsons finished successfully.")
            return True
        except (ParsingError, DataTransformationError, FileWritingError) as ex:
            logging.error("Failed to update version jsons. %s", ex)
            return False
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Encountered unexpected exception: %s", ex)
            return False


def run_data_transformation(config: Config) -> bool:
    """
    Run full data transformation. Creates current files, deletes old ones.
    :param config: App configuration.
    :return: True if all subparts finished successfully.
    """
    logging.info("Starting data transformation.")

    crunched_csv_path = _assemble_crunched_csv_path(config)
    factor_hierarchy_path = find_older_factor_hierarchy_file(config.filepaths.output_root_path)

    success = True
    success &= DataTransformManager.create_default_plot_data(config, crunched_csv_path)
    success &= DataTransformManager.create_distribution_data(config, crunched_csv_path)
    if config.data_transformation_skip_plot_settings:
        success &= DataTransformManager.copy_default_plot_settings(config)
    else:
        success &= DataTransformManager.create_default_plot_settings(config, crunched_csv_path, factor_hierarchy_path)
    success &= DataTransformManager.create_updated_factor_hierarchy(config, crunched_csv_path, factor_hierarchy_path)
    success &= DataTransformManager.create_updated_versions_jsons(config)

    logging.info("Data transformation %s.", "finished successfully" if success else "failed")
    return success


def _assemble_crunched_csv_path(config: Config) -> str:
    crunched_csv_name = f"{config.current_formatted_date}_crunched.csv"
    if config.run_data_transformation_only and config.crunched_csv_name_for_data_transformation_only:
        crunched_csv_name = config.crunched_csv_name_for_data_transformation_only
    crunched_csv_path = path.join(config.filepaths.output_root_path, crunched_csv_name)
    return crunched_csv_path
