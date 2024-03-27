import logging
import os
import shutil

from src.generic_file_handlers.json_file_writer import write_json_file
from src.exception import FileWritingError
from src.models.transformed import DefaultPlotData
from src.utils import find_matching_subfolders


DEFAULT_PLOT_DATA_SUFFIX = "DefaultPlotData"


def create_default_plot_data_files(
    default_plot_data_list: list[DefaultPlotData], output_folder_filepath: str, current_date_prefix: str
) -> None:
    """
    Create json files for default plot data in given output location.
    :param default_plot_data_list: List of default plot data to write into json files.
    :param output_folder_filepath: Path to the output files.
    :param current_date_prefix: Current date formatted as 20240101 from the config to be used in foldername.
    :raises FileWritingError: In case of json serialization or file writing issues.
    """
    try:
        subfolder_filepath = os.path.join(output_folder_filepath, f"{current_date_prefix}_{DEFAULT_PLOT_DATA_SUFFIX}")
        if not os.path.exists(subfolder_filepath):
            os.mkdir(subfolder_filepath)
            logging.info("Created subfolder %s.", subfolder_filepath)

        for default_plot_data in default_plot_data_list:
            filepath = os.path.join(
                subfolder_filepath, f"{default_plot_data.x_factor.value}+{default_plot_data.y_factor.value}.json"
            )
            write_json_file(filepath, default_plot_data.to_dict())

        logging.info(
            "Successfully saved %s default plot data files into %s.", len(default_plot_data_list), subfolder_filepath
        )
    except OSError as ex:
        raise FileWritingError(f"Default plot data creation failed: {ex}") from ex


def delete_old_default_plot_data_files(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Delete other default plot data files left from previous runs that were not the ones created in this run
    (with today's date in filename).
    :param output_folder_path:
    :param current_date_prefix: Current date formatted as 20240101 - only folders with this prefix will not be deleted.
    """
    default_plot_data_folders = find_matching_subfolders(output_folder_path, DEFAULT_PLOT_DATA_SUFFIX)
    for foldername in default_plot_data_folders:
        if current_date_prefix in foldername:
            continue

        full_folder_path = os.path.join(output_folder_path, foldername)
        shutil.rmtree(full_folder_path)
        logging.info("Deleted old '%s'.", full_folder_path)
