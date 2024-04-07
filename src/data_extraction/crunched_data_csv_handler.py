import logging
import os
from os import path
from typing import Optional

import pandas as pd

from src.config import Config
from src.generic_file_handlers.csv_handler import load_csv_as_dataframe
from src.models import CSV_INVALID_VALUE_STRING
from src.utils import find_matching_files


def try_to_load_previous_crunched_df(config: Config) -> Optional[pd.DataFrame]:
    """
    Attempt to load previous crunched df based on path specified in config. If unsuccessful, return None.
    :param config:
    :return: Loaded dataframe, or None.
    """
    if path.exists(config.filepaths.old_crunched_csv) and not config.force_complete_data_extraction:
        df = load_csv_as_dataframe(config.filepaths.old_crunched_csv)
        logging.info("Loaded older dataframe from %s to be updated this run.", config.filepaths.old_crunched_csv)
        return df
    if not config.force_complete_data_extraction:
        logging.warning(
            "Did not find previous crunched csv in location '%s' even though it was expected. Crunched "
            "csv will be created anew only with pdb ids processed this run - this may be not desirable!",
            config.filepaths.old_crunched_csv,
        )
    return None


def create_csv_crunched_data(protein_data_df: pd.DataFrame, output_files_folder: str, current_date_prefix: str) -> None:
    """
    Write given dataframe into csv format files.
    :param protein_data_df: Dataframe with data.
    :param output_files_folder: Folder into which to save the data.
    :param current_date_prefix: Current date formatted as 20240101 for naming purposes.
    """
    filepath_version_one = path.join(output_files_folder, f"{current_date_prefix}_crunched.csv")
    filepath_version_two = path.join(output_files_folder, "data.csv")
    try:
        protein_data_df.to_csv(
            filepath_version_one, index=False, sep=";", encoding="utf8", na_rep=CSV_INVALID_VALUE_STRING
        )
        protein_data_df.to_csv(
            filepath_version_two, index=False, sep=";", encoding="utf8", na_rep=CSV_INVALID_VALUE_STRING
        )
        logging.info("Successfully saved crunched data into '%s' and '%s'.", filepath_version_one, filepath_version_two)
    except OSError as ex:
        logging.error("Failed to save to file: %s", ex)


def create_xlsx_crunched_data(protein_data_df: pd.DataFrame, output_files_folder: str) -> None:
    """
    Write given dataframe into xlsx format file.
    :param protein_data_df: Dataframe to save into file.
    :param output_files_folder: Folder into which to save it.
    """
    filepath = path.join(output_files_folder, "data.xlsx")
    try:
        protein_data_df.to_excel(filepath, index=False, na_rep=CSV_INVALID_VALUE_STRING)
        logging.info("Successfully saved crunched datat into '%s'.", filepath)
    except OSError as ex:
        logging.error("Failed to save to file: %s", ex)


def delete_old_crunched_csv(output_folder_path: str, current_date_prefix: str) -> None:
    """
    Delete other crunched csvs left from previous runs that were not the ones created in this run
    (with today's date in filename).
    :param output_folder_path:
    :param current_date_prefix: Current date formatted as 20240101 - only files with this prefix will not be deleted.
    """
    plot_settings_files = find_matching_files(output_folder_path, "_crunched.csv")
    for filename in plot_settings_files:
        if current_date_prefix in filename:
            continue

        full_filepath = os.path.join(output_folder_path, filename)
        os.remove(full_filepath)
        logging.info("Deleted old '%s'.", full_filepath)
