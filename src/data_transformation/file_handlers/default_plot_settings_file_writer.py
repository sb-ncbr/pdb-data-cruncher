import logging
import os

from src.generic_file_handlers.json_file_writer import write_json_file
from src.exception import FileWritingError, DataTransformationError
from src.models.transformed import DefaultPlotSettingsItem
from src.utils import find_matching_files


DEFAULT_PLOT_SETTINGS_SUFFIX = "DefaultPlotSettings.json"


def create_default_plot_settings_file(
    default_plot_settings: list[DefaultPlotSettingsItem], output_folder_filepath: str, current_date_prefix: str
) -> None:
    """
    Create json file with default plot settings in given location.
    :param default_plot_settings: List of default plot settings item to save into file.
    :param output_folder_filepath: Path to the output files.
    :param current_date_prefix: Current date formatted as 20240101 from the config to be used in filename.
    :raises FileWritingError: In case of json serialization or file writing issues.
    """
    try:
        filepath = os.path.join(output_folder_filepath, f"{current_date_prefix}_{DEFAULT_PLOT_SETTINGS_SUFFIX}")
        default_plot_settings_json = [item.to_dict() for item in default_plot_settings]
        write_json_file(filepath, default_plot_settings_json)
        logging.info("Saved default plot settings for %s factors files into %s.", len(default_plot_settings), filepath)
    except OSError as ex:
        raise FileWritingError(f"Default plot settings creation failed: {ex}") from ex


def rename_default_plot_settings_to_current_date(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Rename first found old plot settings file to a name with current date. (There should be only one such file present,
    but that is not enforced.)
    :param output_folder_path:
    :param current_date_prefix: Current date prefix in format of 20240101 to be used in new file name.
    """
    plot_settings_files = find_matching_files(output_folder_path, DEFAULT_PLOT_SETTINGS_SUFFIX)
    if len(plot_settings_files) == 0:
        raise DataTransformationError(
            f"No previously created default plot settings with '{DEFAULT_PLOT_SETTINGS_SUFFIX}' in name was found to "
            f"be copied. Try running the app without skipping the default plot settings creation."
        )

    old_file_full_path = os.path.join(output_folder_path, plot_settings_files[0])
    new_file_full_path = os.path.join(output_folder_path, f"{current_date_prefix}_{DEFAULT_PLOT_SETTINGS_SUFFIX}")
    os.rename(old_file_full_path, new_file_full_path)


def delete_old_default_plot_settings_files(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Delete other default plot settings files left from previous runs that were not the ones created in this run
    (with today's date in filename).
    :param output_folder_path:
    :param current_date_prefix: Current date formatted as 20240101 - only files with this prefix will not be deleted.
    """
    plot_settings_files = find_matching_files(output_folder_path, DEFAULT_PLOT_SETTINGS_SUFFIX)
    for filename in plot_settings_files:
        if current_date_prefix in filename:
            continue

        full_filepath = os.path.join(output_folder_path, filename)
        os.remove(full_filepath)
        logging.info("Deleted old '%s'.", full_filepath)
