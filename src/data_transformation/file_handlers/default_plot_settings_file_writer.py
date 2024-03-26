import logging
from os import path

from src.generic_file_handlers.json_file_writer import write_json_file
from src.exception import FileWritingError
from src.models.transformed import DefaultPlotSettingsItem
from src.utils import get_formatted_date


def create_default_plot_settings_file(
    default_plot_settings: list[DefaultPlotSettingsItem], output_folder_filepath: str
) -> None:
    """
    Create json file with default plot settings in given location.
    :param default_plot_settings: List of default plot settings item to save into file.
    :param output_folder_filepath: Path to the output files.
    :raises FileWritingError: In case of json serialization or file writing issues.
    """
    try:
        filepath = path.join(output_folder_filepath, f"{get_formatted_date()}_DefaultPlotSettings.json")
        default_plot_settings_json = [item.to_dict() for item in default_plot_settings]
        write_json_file(filepath, default_plot_settings_json)
        logging.info(
            "Saved default plot settings for %s factors files into %s.", len(default_plot_settings), filepath
        )
    except OSError as ex:
        raise FileWritingError(f"Default plot settings creation failed: {ex}") from ex
