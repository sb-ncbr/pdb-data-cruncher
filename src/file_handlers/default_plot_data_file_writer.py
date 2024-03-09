import json
import logging
from io import BytesIO
from os import path
from zipfile import ZipFile

from src.models.transformed import DefaultPlotData
from src.utils import get_formatted_date
from src.exception import FileWritingError


def write_default_plot_data_into_zip(default_plot_data: list[DefaultPlotData], location_filepath: str) -> None:
    """
    Takes the default plot data and saves it in given location path into a zip archive. The resulting zip archive
    contains subfolder named with today's date and inside which are json files with content representing each
    default plot data.
    :param default_plot_data: List of default plot data to write into the archive.
    :param location_filepath: Path where the resulting zip archive will be saved.
    :raises FileWritingError: In case of json seriealization or file permission issues.
    """
    subfolder_name = f"{get_formatted_date()}_DefaultPlotData"
    zip_archive_path = path.join(location_filepath, "DefaultPlotData.zip")
    zip_buffer = BytesIO()

    try:
        # load default plot data into the zip buffer as individual files
        with ZipFile(zip_buffer, "w") as zip_file:
            for plot_data in default_plot_data:
                file_contents = json.dumps(plot_data.to_dict(), indent="\t")
                filepath_partial = path.join(
                    subfolder_name, f"{plot_data.x_factor.value}+{plot_data.y_factor.value}.json"
                )
                zip_file.writestr(filepath_partial, file_contents)

        # save the zip archive
        with open(zip_archive_path, "wb") as zip_out_file:
            zip_out_file.write(zip_buffer.getvalue())
    except IOError as ex:
        raise FileWritingError(f"Failed to create default plot data zip archive: {ex}") from ex

    logging.info(
        "Successfully saved default plot data in %s. It contains %s default plot data jsons.",
        zip_archive_path,
        len(default_plot_data),
    )
