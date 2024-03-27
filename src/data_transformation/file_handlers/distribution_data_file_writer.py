import logging
import os
import shutil

from src.generic_file_handlers.json_file_writer import write_json_file
from src.models.transformed import DistributionData
from src.exception import FileWritingError
from src.utils import find_matching_subfolders


DISTRIBUTION_DATA_SUFFIX = "DistributionData"


def create_distribution_data_files(
    distribution_data_list: list[DistributionData], output_folder_filepath: str, current_date_prefix: str
) -> None:
    """
    Create json files for distribution data in given output location.
    :param distribution_data_list: List of distribution data to write into json files.
    :param output_folder_filepath: Path to the output files.
    :param current_date_prefix: Current date formatted as 20240101 from the config to be used in folder name.
    :raises FileWritingError: In case of json serialization or file writing issues.
    """
    try:
        subfolder_filepath = os.path.join(output_folder_filepath, f"{current_date_prefix}_{DISTRIBUTION_DATA_SUFFIX}")
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


def delete_old_distribution_data_files(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Delete other distribution data files left from previous runs that were not the ones created in this run
    (with today's date in filename).
    :param output_folder_path:
    :param current_date_prefix: Current date formatted as 20240101 - only folders with this prefix will not be deleted.
    """
    distribution_data_folders = find_matching_subfolders(output_folder_path, DISTRIBUTION_DATA_SUFFIX)
    for foldername in distribution_data_folders:
        if current_date_prefix in foldername:
            continue

        full_folder_path = os.path.join(output_folder_path, foldername)
        shutil.rmtree(full_folder_path)
        logging.info("Deleted old '%s'.", full_folder_path)
