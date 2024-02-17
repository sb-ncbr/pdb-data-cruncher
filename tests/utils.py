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


def strings_are_equal_respecting_floats(first_string: str, second_string: str, float_precision: float = 1e-3) -> bool:
    """
    Compares given values as strings. If the strings are with ".", representing float values,
    it also tries to compare them as float values.
    :param first_string: String with first value to compare.
    :param second_string: String with second value to compare.
    :param float_precision: Maximum difference of floats that will still be considered as the same value.
    :return: Bool if they are the same (given float_precision if they are floats), or not.
    """
    if first_string == second_string:
        # no need to try converting if they are the same already
        return True

    try:
        # try to compare them as floats
        first_as_float = to_float(first_string)
        second_as_float = to_float(second_string)
        if first_as_float is not None and second_as_float is not None:
            return second_as_float == pytest.approx(first_as_float, rel=float_precision)
    except (ValueError, TypeError):
        # not floats or cannot be converted and pure compare already failed -> not the same
        return False
