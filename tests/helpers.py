from typing import Optional, Any

import pytest
import dataclasses


def compare_dataclasses(
    actual: dataclasses.dataclass, expected: dataclasses.dataclass, ignored_fields: Optional[list] = None
) -> list[tuple[str, Any, Any]]:
    """
    Compares all fields of given dataclasses. Takes into account imprecise nature of floats.
    :param actual: Dataclass instance produced by the test.
    :param expected: Expected value of dataclass instance.
    :param ignored_fields: List of field names to ignore.
    :return: List of tuples consisting of differences in classes in format
    (field_name, actual_value and expect_values).
    """
    differences = []
    ignored_fields = ignored_fields if ignored_fields else []

    for field_name, actual_value in dataclasses.asdict(actual).items():
        expected_value = getattr(expected, field_name, None)
        if field_name in ignored_fields:
            continue
        if type(actual_value) is float:
            if expected_value != pytest.approx(actual_value, abs=1e-3):
                differences.append((field_name, actual_value, expected_value))
        else:
            if actual_value != expected_value:
                differences.append((field_name, actual_value, expected_value))

    return differences
