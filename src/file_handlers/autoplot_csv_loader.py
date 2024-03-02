import logging

import pandas as pd

from src.models.transformed import FactorPair
from src.utils import get_factor_type


def load_autoplot_factor_pairs(filepath: str) -> list[FactorPair]:
    """
    Load X and Y factors as factor pairs from autoplot csv.
    :param filepath: Path to the autoplot.
    :return: List of autoplot pairs. Each factor is represented as FactorType.
    :raises ParsingError: In case of unrecoverable parsing error.
    """
    df = pd.read_csv(filepath, delimiter=";", usecols=["X", "Y"])
    factor_pairs = []

    for x_factor_string, y_factor_string in zip(df["X"], df["Y"]):
        x_factor_type = get_factor_type(x_factor_string)
        y_factor_type = get_factor_type(y_factor_string)
        if x_factor_type is None or y_factor_type is None:
            logging.error(
                f"Autoplot.csv failed to extract XY factor pair because such string values were not found "
                f"in allowed FactorTypes. X: '{x_factor_string}', Y: '{y_factor_string}'. Row skipped."
            )
            continue
        factor_pairs.append(FactorPair(
            x_factor=x_factor_type,
            y_factor=y_factor_type,
        ))

    return factor_pairs
