from dataclasses import dataclass, field, asdict
from typing import Optional, Any

import pytest

from src.utils import to_float


@dataclass(slots=True)
class Difference:
    """
    One difference (in one field) between two dataclasses.
    """

    item_name: str
    expected_value: Optional[Any]
    actual_value: Optional[Any]


@dataclass(slots=True)
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
            [f"{diff.item_name}: expected {diff.expected_value}, got {diff.actual_value}" for diff in self.items]
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


def compare_lists_of_string_with_float_imprecision(
    actual: list[str],
    expected: list[str],
    float_precision: float = 1e-3,
) -> Differences:
    """
    Compares all items in given lists with string values. If the strings are with ".", representing float values,
    it also tries to compare them as float values.
    :param actual: List representing actual result.
    :param expected: List representing expected result.
    :param float_precision: Maximum difference of floats that will still be considered as the same value.
    :return: Found differences object.
    """
    differences = Differences()
    if len(actual) != len(expected):
        differences.items.append(Difference("list length", len(expected), len(actual)))

    for index, (actual_value, expected_value) in enumerate(zip(actual, expected)):
        if "." in actual_value or "." in expected_value:
            actual_float = to_float(actual_value)
            expected_float = to_float(expected_value)
            if actual_float is not None and expected_float is not None:
                # compare as floats, then continue
                if expected_float != pytest.approx(actual_float, rel=float_precision):
                    differences.items.append(Difference(f"item index {index}", expected_value, actual_value))
                continue
        # not floats or cannot be converted -> normal comparison
        if actual_value != expected_value:
            differences.items.append(Difference(f"item index {index}", expected_value, actual_value))

    return differences
