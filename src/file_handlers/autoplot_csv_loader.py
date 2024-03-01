import logging
from dataclasses import dataclass, fields
from typing import Generator, Union, Optional
import csv

from src.exception import ParsingError
from src.utils import to_int, to_float, to_bool, to_int_or_float, get_factor_type
from src.models.transformed import FactorPair


@dataclass(slots=True)
class AutoplotCsvItem:
    """
    Item representing relevant information from autoplot csv row.
    """
    # TODO remove those i don't need (perhaps only need factor_on_x and factor_on_y pairs)
    factor_on_x: str  # line[0]
    factor_on_y: str  # line[1]
    bucket_style: str  # line[2]
    bucket_number: float  # line[3]
    valid_value_metric_filter: int  # line[4]
    nonzero_value_metric_filter: int  # line[5]
    x_metric_range_limitation: bool  # line[6]
    x_limit_from: Union[int, float]  # line[7]
    x_limit_to: Union[int, float]  # line[8]
    y_metric_range_limitation: bool  # line[9]
    y_limit_from: Union[int, float]  # line[10]
    y_limit_to: Union[int, float]  # line[11]
    dont_plot_minimum_maximum: bool  # line[12]
    graph_width: int  # line[13]
    graph_height: int  # line[14]
    filename: str  # line[15]

    @property
    def values_missing(self) -> int:
        """
        Returns the number of values that are none among the class fields.
        :return: Number of values, that are None.
        """
        return sum(field is None for field in fields(self))


def autoplot_csv_generator(filepath: str) -> Generator[AutoplotCsvItem, None, None]:
    """
    Creates a generator for reading autoplot.csv files, that supplies row items one by one.
    :param filepath: Path to autoplot csv.
    :return: Generator.
    """
    try:
        with open(filepath, encoding="utf8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            _ = next(csv_reader)  # skip header row
            for row in csv_reader:
                autoplot_item = _create_autoplot_csv_item(row)
                if autoplot_item is None:
                    continue
                yield autoplot_item
    except OSError as ex:
        raise ParsingError("Autoplot.csv cannot be read") from ex


def load_autoplot_factor_pairs(filepath: str) -> list[FactorPair]:
    """
    Load X and Y factors as factor pairs from autoplot csv.
    :param filepath: Path to the autoplot.
    :return: List of autoplot pairs. Each factor is represented as FactorType.
    :raises ParsingError: In case of unrecoverable parsing error.
    """
    try:
        with open(filepath, encoding="utf8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            header_row = next(csv_reader)
            # check header is as expected
            if header_row[0] != "X" or header_row[1] != "Y":
                raise ParsingError(
                    f"X and Y expected in the first two columns, but got {header_row[0]} and {header_row[1]} instead."
                )
            autoplot_factor_pairs = _load_autoplot_factor_pairs_from_body_only(csv_reader)
            logging.debug("Autoplot factor pairs loaded. %s pairs loaded.", len(autoplot_factor_pairs))
            return autoplot_factor_pairs
    except OSError as ex:
        raise ParsingError("Autoplot.csv cannot be read") from ex
    except IndexError as ex:
        raise ParsingError("Autoplot.csv could not be parsed: too short lines with values") from ex


def _load_autoplot_factor_pairs_from_body_only(csv_reader: csv.reader) -> list[FactorPair]:
    factor_pairs = []

    for row in csv_reader:
        x_factor_type = get_factor_type(row[0])
        y_factor_type = get_factor_type(row[1])
        if x_factor_type is None or y_factor_type is None:
            logging.error(
                f"Autoplot.csv failed to extract XY factor pair because such string values were not found "
                f"in allowed FactorTypes. X: '{row[0]}', Y: '{row[1]}'. Row skipped."
            )
            continue
        factor_pairs.append(FactorPair(
            x_factor=x_factor_type,
            y_factor=y_factor_type,
        ))

    return factor_pairs


def _create_autoplot_csv_item(row: list[str]) -> Optional[AutoplotCsvItem]:
    if len(row) < 16:
        logging.warning("Autoplot row has less than 16 items (had %s), it was skipped! Full row: %s", len(row), row)
        return None

    autoplot_csv_item = AutoplotCsvItem(
        factor_on_x=row[0],
        factor_on_y=row[1],
        bucket_style=row[2],
        bucket_number=to_float(row[3]),
        valid_value_metric_filter=to_int(row[4]),
        nonzero_value_metric_filter=to_int(row[5]),
        x_metric_range_limitation=to_bool(row[6]),
        x_limit_from=to_int_or_float(row[7]),
        x_limit_to=to_int_or_float(row[8]),
        y_metric_range_limitation=to_bool(row[9]),
        y_limit_from=to_int_or_float(row[10]),
        y_limit_to=to_int_or_float(row[11]),
        dont_plot_minimum_maximum=to_bool(row[12]),
        graph_width=to_int(row[13]),
        graph_height=to_int(row[14]),
        filename=row[15],
    )

    if autoplot_csv_item.values_missing > 0:
        logging.warning(
            "Row of autoplot contains empty values or some values failed to convert. Skipping this row! Values "
            "missing: %s. Full row: %s.",
            autoplot_csv_item.values_missing,
            row
        )
        return None

    return autoplot_csv_item
