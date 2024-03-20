from functools import lru_cache

import pandas as pd

from src.exception import ParsingError


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
