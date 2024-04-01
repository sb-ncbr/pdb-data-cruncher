import logging
from functools import lru_cache

import pandas as pd

from src.exception import ParsingError, FileWritingError
from src.models import CSV_INVALID_VALUE_STRING


@lru_cache()
def load_csv_as_dataframe(filepath: str) -> pd.DataFrame:
    """
    Load csv as pandas dataframe (expecting ; delimiter).
    :param filepath: Path to csv file.
    :return: Pandas dataframe.
    """
    try:
        return pd.read_csv(filepath, delimiter=";")
    except (ValueError, OSError) as ex:
        raise ParsingError(f"Failed to load {filepath} csv. {ex}") from ex


def save_dataframe_to_csv(dataframe: pd.DataFrame, filepath: str) -> None:
    """
    Save dataframe into csv.
    :param dataframe:
    :param filepath:
    :raises FileWritingError:
    """
    try:
        dataframe.to_csv(filepath, index=False, sep=";", encoding="utf8", na_rep=CSV_INVALID_VALUE_STRING)
        logging.info("Successfully saved csv into '%s'.", filepath)
    except OSError as ex:
        raise FileWritingError(f"Failed to save csv into {filepath}. {ex}") from ex
