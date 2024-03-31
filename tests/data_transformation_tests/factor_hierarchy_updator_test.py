from decimal import Decimal

import pandas as pd
import pytest

from src.exception import DataTransformationError
from src.config import FactorHierarchyConfig
from src.data_transformation.factor_hierarchy_updater import update_factor_hierarchy
from src.models import FactorType


TEST_CONFIG = FactorHierarchyConfig(
    min_interval_count=10,
    ideal_interval_count=100,
    max_interval_count=100,
    allowed_slider_base_sizes=[10, 20, 25, 50]
)


FACTOR_NAMES_TRANSLATION = {
    FactorType.RELEASE_DATE: "year of release",
    FactorType.RESOLUTION: "structure resolution [A]",
}


def create_minimal_df(min_value, max_value, factor_type: FactorType) -> pd.DataFrame:
    dummy_pdb_ids = ["xxxx", "xxxx"]
    values = [min_value, max_value]
    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        factor_type.value: values,
    })


@pytest.mark.parametrize(
    "factor_type, data_min, data_max, expected_min_value, expected_max_value, expected_slider_step",
    [
        (FactorType.RESOLUTION, 10, 20, "10", "20", "0.1"),  # basic test
        (FactorType.RESOLUTION, 10.9, 19.1, "10", "20", "0.1"),  # test values get floored/ceiled
        (FactorType.RESOLUTION, 88, 123000, "0", "130000", "2000"),  # test big value with small one
        (FactorType.RESOLUTION, 0.0008, 0.123, "0", "0.13", "0.002"),  # test small numbers rounding
        (FactorType.RELEASE_DATE, 1955, 2005, "1955", "2005", "1"),  # year does not get rounded
    ]
)
def test_basic_factor_hierarchy_gets_updated_correctly(
    factor_type, data_min, data_max, expected_min_value, expected_max_value, expected_slider_step
):
    minimal_factor_hierarchy = {
        "FactorList": [{
            "FactorName": FACTOR_NAMES_TRANSLATION[factor_type],
        }]
    }
    minimal_crunched_df = create_minimal_df(data_min, data_max, factor_type)
    # act
    update_factor_hierarchy(minimal_factor_hierarchy, minimal_crunched_df, FACTOR_NAMES_TRANSLATION, TEST_CONFIG)
    # assert
    factor_json = minimal_factor_hierarchy["FactorList"][0]
    assert Decimal(factor_json["ValueRangeFrom"]) == Decimal(expected_min_value)  # test Decimal to avoid .0 issues
    assert Decimal(factor_json["ValueRangeTo"]) == Decimal(expected_max_value)
    assert Decimal(factor_json["SliderStep"]) == Decimal(expected_slider_step)


def test_nonexistent_factor_name_raises():
    incorrect_factor_hierarchy = {
        "FactorList": [{
            "FactorName": "non existent factor",
        }]
    }
    minimal_crunched_df = pd.DataFrame()

    with pytest.raises(DataTransformationError):
        update_factor_hierarchy(incorrect_factor_hierarchy, minimal_crunched_df, FACTOR_NAMES_TRANSLATION, TEST_CONFIG)


def test_factor_hierarchy_with_wrong_structure_raises():
    wrong_factor_hierarchy = {}
    minimal_crunched_df = create_minimal_df(10, 20, FactorType.RESOLUTION)

    with pytest.raises(DataTransformationError):
        update_factor_hierarchy(wrong_factor_hierarchy, minimal_crunched_df, FACTOR_NAMES_TRANSLATION, TEST_CONFIG)


def test_only_one_value_raises():
    minimal_factor_hierarchy = {
        "FactorList": [{
            "FactorName": FACTOR_NAMES_TRANSLATION[FactorType.RESOLUTION],
        }]
    }
    minimal_crunched_df = create_minimal_df(10, 10, FactorType.RESOLUTION)

    with pytest.raises(DataTransformationError):
        update_factor_hierarchy(minimal_factor_hierarchy, minimal_crunched_df, FACTOR_NAMES_TRANSLATION, TEST_CONFIG)
