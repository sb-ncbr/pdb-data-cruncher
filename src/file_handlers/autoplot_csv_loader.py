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
    factor_pair_duplicates = set()

    for x_factor_string, y_factor_string in zip(df["X"], df["Y"]):
        x_factor_type = get_factor_type(x_factor_string)
        y_factor_type = get_factor_type(y_factor_string)
        if x_factor_type is None or y_factor_type is None:
            logging.error(
                "Autoplot.csv failed to extract XY factor pair because such string values were not found "
                "in allowed FactorTypes. X: '%s', Y: '%s'. Row skipped.",
                x_factor_string,
                y_factor_string,
            )
            continue
        factor_pair = FactorPair(
            x=x_factor_type,
            y=y_factor_type,
        )
        if factor_pair in factor_pairs:
            factor_pair_duplicates.add(f"{factor_pair.x.value}+{factor_pair.y.value}")
        else:
            factor_pairs.append(factor_pair)

    if len(factor_pair_duplicates) > 0:
        logging.warning(
            "In autoplot csv, %s factor pairs were present multiple times. Only one copy will be processed. "
            "Duplicate pairs: %s",
            len(factor_pair_duplicates),
            ", ".join(factor_pair_duplicates),
        )

    return factor_pairs
