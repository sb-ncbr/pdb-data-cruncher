import logging
import os

from src.generic_file_handlers.json_file_writer import write_json_file
from src.exception import FileWritingError
from src.models.transformed import DefaultPlotData
from src.utils import get_formatted_date


def create_default_plot_data_files(default_plot_data_list: list[DefaultPlotData], output_folder_filepath: str) -> None:
    """
    Create json files for default plot data in given output location.
    :param default_plot_data_list: List of default plot data to write into json files.
    :param output_folder_filepath: Path to the output files.
    :raises FileWritingError: In case of json serialization or file writing issues.
    """
    try:
        subfolder_filepath = os.path.join(output_folder_filepath, f"{get_formatted_date()}_DefaultPlotData")
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
