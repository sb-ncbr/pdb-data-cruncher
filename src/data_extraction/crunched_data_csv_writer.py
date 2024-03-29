import logging
from os import path

import pandas as pd

from src.models import CSV_INVALID_VALUE_STRING
from src.utils import get_formatted_date


def create_csv_crunched_data(protein_data_df: pd.DataFrame, output_files_folder: str) -> None:
    """
    Write given dataframe into csv format files.
    :param protein_data_df: Dataframe with data.
    :param output_files_folder: Folder into which to save the data.
    """
    filepath_version_one = path.join(output_files_folder, f"{get_formatted_date()}_crunched.csv")
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
        protein_data_df.to_excel(filepath, index=False, na_rep="nan")
        logging.info("Successfully saved crunched datat into '%s'.", filepath)
    except OSError as ex:
        logging.error("Failed to save to file: %s", ex)
