from dataclasses import dataclass, field, asdict
from typing import Optional, Any

import pytest


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
