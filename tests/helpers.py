import dataclasses
from typing import Optional, Any

import pytest


def compare_dataclasses(
    actual: dataclasses.dataclass,
    expected: dataclasses.dataclass,
    ignored_fields: Optional[list[str]] = None,
    float_precision: float = 1e-3
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
            if expected_value != pytest.approx(actual_value, abs=float_precision):
                differences.append((field_name, expected_value, actual_value))
        else:
            if actual_value != expected_value:
                differences.append((field_name, expected_value, actual_value))

    return differences
