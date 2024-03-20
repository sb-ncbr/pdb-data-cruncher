import logging
import os

from src.file_handlers.json_file_writer import write_json_file
from src.utils import get_formatted_date
from src.models.transformed import DistributionData
from src.exception import FileWritingError


def create_distribution_data_files(distribution_data_list: list[DistributionData], output_folder_filepath: str) -> None:
    """
    Create json files for distribution data in given output location.
    :param distribution_data_list: List of distribution data to write into json files.
    :param output_folder_filepath: Path to the output files.
    :raises FileWritingError: In case of json serialization or file writing issues.
    """
    try:
        subfolder_filepath = os.path.join(output_folder_filepath, f"{get_formatted_date()}_DistributionData")
        if not os.path.exists(subfolder_filepath):
            os.mkdir(subfolder_filepath)
            logging.info("Created subfolder %s.", subfolder_filepath)

        for distribution_data in distribution_data_list:
            filepath = os.path.join(subfolder_filepath, f"{distribution_data.factor_type.value}.json")
            write_json_file(filepath, distribution_data.to_dict())

        logging.info(
            "Successfully saved %s distribution data files into %s.", len(distribution_data_list), subfolder_filepath
        )
    except OSError as ex:
        raise FileWritingError(f"Distribution data creation failed: {ex}") from ex
