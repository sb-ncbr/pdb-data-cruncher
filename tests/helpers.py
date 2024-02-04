import csv
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

import pytest

from tests.test_constants import CRUNCHED_RESULTS_CSV_PATH


@dataclass
class Difference:
    """
    One difference (in one field) between two dataclasses.
    """

    field_name: str
    expected_value: Optional[Any]
    actual_value: Optional[Any]


@dataclass
class Differences:
    """
    Class holding information about differences between two dataclasses.
    """

    items: list[Difference] = field(default_factory=list)

    @property
    def count(self):
        return len(self.items)

    def get_difference_description(self) -> str:
        return " | ".join(
            [f"{diff.field_name}: expected {diff.expected_value}, got {diff.actual_value}" for diff in self.items]
        )


def compare_dataclasses(
    actual: dataclass,
    expected: dataclass,
    ignored_fields: Optional[list[str]] = None,
    float_precision: float = 1e-3,
) -> Differences:
    """
    Compares all fields of given dataclasses. Takes into account imprecise nature of floats.
    :param actual: Dataclass instance produced by the test.
    :param expected: Expected value of dataclass instance.
    :param ignored_fields: List of field names to ignore.
    :param float_precision: Maximum difference of floats that will still be considered as the same value.
    :return: Found differences object.
    """
    differences = Differences()
    ignored_fields = ignored_fields if ignored_fields else []

    for field_name, actual_value in asdict(actual).items():
        expected_value = getattr(expected, field_name, None)
        if field_name in ignored_fields:
            continue
        if isinstance(actual_value, float) or isinstance(expected_value, float):
            if expected_value != pytest.approx(actual_value, rel=float_precision):
                differences.items.append(Difference(field_name, expected_value, actual_value))
        else:
            if actual_value != expected_value:
                differences.items.append(Difference(field_name, expected_value, actual_value))

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
        raise RuntimeError(f"{len(not_found_fields)} fields not found in csv file: {not_found_fields}")

    return extracted_fields
