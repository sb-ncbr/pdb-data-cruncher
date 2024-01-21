import csv
import dataclasses
from typing import Optional, Any

import pytest

from tests.test_constants import CRUNCHED_RESULTS_CSV_PATH


def compare_dataclasses(
    actual: dataclasses.dataclass,
    expected: dataclasses.dataclass,
    ignored_fields: Optional[list[str]] = None,
    float_precision: float = 1e-3,
) -> list[tuple[str, Any, Any]]:
    """
    Compares all fields of given dataclasses. Takes into account imprecise nature of floats.
    :param actual: Dataclass instance produced by the test.
    :param expected: Expected value of dataclass instance.
    :param ignored_fields: List of field names to ignore.
    :param float_precision: Maximum difference of floats that will still be considered as the same value.
    :return: List of tuples consisting of differences in classes in format
    (field_name, actual_value and expect_values).
    """
    differences = []
    ignored_fields = ignored_fields if ignored_fields else []

    for field_name, actual_value in dataclasses.asdict(actual).items():
        expected_value = getattr(expected, field_name, None)
        if field_name in ignored_fields:
            continue
        if isinstance(actual_value, float):
            if expected_value != pytest.approx(actual_value, rel=float_precision):
                differences.append((field_name, expected_value, actual_value))
        else:
            if actual_value != expected_value:
                differences.append((field_name, expected_value, actual_value))

    return differences


def load_data_from_crunched_results_csv(pdb_id: str, fields: list[str]) -> dict[str, str]:
    """
    Loads data from crunched_results.csv and returns only relevant field values.
    :param pdb_id: PDB ID of structure data to load.
    :param fields: Fields to exctract.
    :return: Dict where keys are given field names, and values are extracted values (as strings).
    :raises RuntimeError: If PDB ID is not found in csv or one or more fields are not found.
    """
    with open(CRUNCHED_RESULTS_CSV_PATH, encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        first_row = next(csv_reader)
        relevant_row = None
        current_row = next(csv_reader)
        while current_row:
            if current_row[0] == pdb_id:
                relevant_row = current_row
                break
            current_row = next(csv_reader)

        if not relevant_row:
            raise RuntimeError(f"Row with pdb_id {pdb_id} not found in csv file.")

    extracted_fields = {}
    for index, field_name in enumerate(first_row):
        if field_name in fields:
            if relevant_row[index] == "nan":
                extracted_fields[field_name] = None
            else:
                extracted_fields[field_name] = relevant_row[index]

    if len(extracted_fields) != len(fields):
        not_found_fields = [field_name for field_name in fields if field_name not in extracted_fields]
        raise RuntimeError(f"One or multiple fields not found in csv file: {not_found_fields}")

    return extracted_fields


def float_or_none(string_value: Optional[str]) -> Optional[float]:
    """
    If None, returns None, if not None, converts to float.
    :param string_value: Value to convert.
    :return: Converted value, or None.
    """
    return float(string_value) if string_value else None


def int_or_none(string_value: Optional[str]) -> Optional[int]:
    """
    If None, returns None, if not None, converts to int.
    :param string_value: Value to convert.
    :return: Converted value, or None.
    """
    return int(string_value) if string_value else None
