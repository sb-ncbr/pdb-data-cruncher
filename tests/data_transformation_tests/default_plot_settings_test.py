import random
from dataclasses import dataclass
from decimal import Decimal

import json
import pandas as pd
import pytest

from src.config import DefaultPlotSettingsConfig
from src.data_transformation.default_plot_settings_creator import create_default_plot_settings
from src.exception import DataTransformationError
from src.models import FactorType
from src.models.transformed import DefaultPlotSettingsItem

TEST_CONFIG = DefaultPlotSettingsConfig()

FACTOR_NAMES_TRANSLATION = {
    FactorType.RELEASE_DATE: "year of release",
    FactorType.RESOLUTION: "structure resolution [A]",
}


@dataclass(slots=True)
class FakeHierarchyItem:
    familiar_name: str
    applicable_for_x: bool
    applicable_for_y: bool

    def to_dict(self):
        return {
            "FactorName": self.familiar_name,
            "ApplicableForX": self.applicable_for_x,
            "ApplicableForY": self.applicable_for_y,
        }


def create_test_hierarchy_json(hierarchy_items: list[FakeHierarchyItem]):
    factor_list = []
    for item in hierarchy_items:
        factor_list.append(item.to_dict())
    return {
        "FactorList": factor_list
    }


def create_test_hierarchy_json_with_release_date_and_resolution():
    return create_test_hierarchy_json([
        FakeHierarchyItem(FACTOR_NAMES_TRANSLATION[FactorType.RELEASE_DATE], True, True),
        FakeHierarchyItem(FACTOR_NAMES_TRANSLATION[FactorType.RESOLUTION], True, True),
    ])


def create_simple_crunched_df():
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    for _ in range(50):
        dummy_pdb_ids.extend(["xxxx", "xxxx", "xxxx"])
        release_date_values.extend([2000, 2001, 2003])
        resolution_values.extend([0.7, 2.0, 10.001])  # TODO

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values
    })


def create_crunched_df_with_only_one_value_in_resolution():
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    for _ in range(25):
        dummy_pdb_ids.extend(["xxxx", "xxxx"])
        release_date_values.extend([2020, 2021])
        resolution_values.extend([2.0, 2.0])

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values
    })


def create_crunched_df_for_3_factor_combinations():
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    atom_count_values = []
    for _ in range(50):
        dummy_pdb_ids.extend(["xxxx", "xxxx", "xxxx"])
        release_date_values.extend([2000, 2001, 2003])
        resolution_values.extend([0.7, 2.0, 10.1])  # TODO
        atom_count_values.extend([10000, 15000, 20000])
        dummy_pdb_ids.append("xxxx")
        release_date_values.append(1990)
        resolution_values.append(None)
        atom_count_values.append(15000)

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values,
        FactorType.ATOM_COUNT.value: atom_count_values,
    })


def create_crunched_df_for_bucket_upsizing():
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    for _ in range(50):
        dummy_pdb_ids.extend(["xxxx", "xxxx", "xxxx"])
        release_date_values.extend([2000, 2001, 2002])
        resolution_values.extend([1.0, 2.0, 3.0])

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values,
    })


@pytest.mark.basic
def test_year_factor_and_normal_factor_creates_a_result():
    hierarchy_json = create_test_hierarchy_json_with_release_date_and_resolution()
    crunched_df = create_simple_crunched_df()
    expected_release_date_settings = DefaultPlotSettingsItem(
       1, "year of release", 2000, 2003
    )
    expected_resolution_settings = DefaultPlotSettingsItem(
        # max value is 10.0 even though there is 10.001 in the data, because the website autofills the last bucket
        # in all cases without consideration whether the limit (10.0) value itself is in the data or not
        Decimal("0.2"), "structure resolution [A]", Decimal("0.60"), Decimal("10.0"),
    )

    plot_settings_list = create_default_plot_settings(
        crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG
    )

    assert plot_settings_list
    assert plot_settings_list[0] == expected_release_date_settings
    assert plot_settings_list[1] == expected_resolution_settings

    print(plot_settings_list[1])


@pytest.mark.basic
def test_multiple_y_factors_affect_min_max_value():
    factor_names_translations = {
        FactorType.RELEASE_DATE: "year of release",
        FactorType.RESOLUTION: "structure resolution [A]",
        FactorType.ATOM_COUNT: "structure atom count (without ligand atoms)",
    }
    hierarchy_json = create_test_hierarchy_json([
        FakeHierarchyItem(factor_names_translations[FactorType.RELEASE_DATE], True, True),
        FakeHierarchyItem(factor_names_translations[FactorType.RESOLUTION], True, True),
        FakeHierarchyItem(factor_names_translations[FactorType.ATOM_COUNT], True, True),
    ])
    # crunched df here has 50x value 1990 in year of release, but with None in resolution - therefore it does
    # get filtered out and does not move min value lower than 2000
    crunched_df = create_crunched_df_for_3_factor_combinations()
    expected_release_date_settings = DefaultPlotSettingsItem(
       1, "year of release", 2000, 2003
    )

    plot_settings_list = create_default_plot_settings(
        crunched_df, factor_names_translations, hierarchy_json, TEST_CONFIG
    )

    assert plot_settings_list
    assert plot_settings_list[0] == expected_release_date_settings


@pytest.mark.basic
def test_y_factor_does_not_affect_min_max_value_if_turned_off_in_hierarchy():
    factor_names_translations = {
        FactorType.RELEASE_DATE: "year of release",
        FactorType.RESOLUTION: "structure resolution [A]",
        FactorType.ATOM_COUNT: "structure atom count (without ligand atoms)",
    }
    hierarchy_json = create_test_hierarchy_json([
        FakeHierarchyItem(factor_names_translations[FactorType.RELEASE_DATE], True, True),
        FakeHierarchyItem(factor_names_translations[FactorType.RESOLUTION], True, False),
        FakeHierarchyItem(factor_names_translations[FactorType.ATOM_COUNT], True, True),
    ])
    # crunched df here has 50x value 1990 in year of release, but with None in resolution ->
    # BUT in this test case, resolution is set to not be applicable on y and therefore 1990 can be min value
    crunched_df = create_crunched_df_for_3_factor_combinations()
    expected_release_date_settings = DefaultPlotSettingsItem(
        1, "year of release", 1990, 2003
    )

    plot_settings_list = create_default_plot_settings(
        crunched_df, factor_names_translations, hierarchy_json, TEST_CONFIG
    )

    assert plot_settings_list
    assert plot_settings_list[0] == expected_release_date_settings


@pytest.mark.basic
def test_bucket_size_is_bigger_than_smallest_possible_when_there_are_too_few_structures():
    hierarchy_json = create_test_hierarchy_json_with_release_date_and_resolution()
    crunched_df = create_crunched_df_for_bucket_upsizing()
    # The smallest possible size of bucket is 0.2, but it will be bigger because buckets of 0.2 do not have enough data
    expected_resolution_settings = DefaultPlotSettingsItem(
        Decimal("1.0"), "structure resolution [A]", Decimal("1.0"), Decimal("3.0"),
    )

    plot_settings_list = create_default_plot_settings(
        crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG
    )

    assert plot_settings_list
    assert plot_settings_list[1] == expected_resolution_settings


@pytest.mark.basic
def test_x_factor_does_not_output_if_turned_off_in_hierarchy():
    hierarchy_json = create_test_hierarchy_json([
        FakeHierarchyItem(FACTOR_NAMES_TRANSLATION[FactorType.RELEASE_DATE], True, True),
        FakeHierarchyItem(FACTOR_NAMES_TRANSLATION[FactorType.RESOLUTION], False, True),
    ])
    crunched_df = create_simple_crunched_df()
    expected_release_date_settings = DefaultPlotSettingsItem(
        1, "year of release", 2000, 2003
    )

    plot_settings_list = create_default_plot_settings(
        crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG
    )

    assert plot_settings_list
    assert len(plot_settings_list) == 1
    assert plot_settings_list[0] == expected_release_date_settings


@pytest.mark.basic
def test_outliers_are_not_taken_into_account():
    hierarchy_json = create_test_hierarchy_json_with_release_date_and_resolution()
    crunched_df = create_simple_crunched_df()
    crunched_df.loc[len(crunched_df)] = {FactorType.RESOLUTION.value: 999.0}
    expected_release_date_settings = DefaultPlotSettingsItem(
        1, "year of release", 2000, 2003
    )
    expected_resolution_settings = DefaultPlotSettingsItem(
        Decimal("0.2"), "structure resolution [A]", Decimal("0.60"), Decimal("10.0"),  # unaffected by 999 outlier
    )

    plot_settings_list = create_default_plot_settings(
        crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG
    )

    assert plot_settings_list
    assert plot_settings_list[0] == expected_release_date_settings
    assert plot_settings_list[1] == expected_resolution_settings


@pytest.mark.basic
def test_no_data_range_throws_exception():
    hierarchy_json = create_test_hierarchy_json_with_release_date_and_resolution()
    crunched_df = create_crunched_df_with_only_one_value_in_resolution()

    with pytest.raises(DataTransformationError):
        _ = create_default_plot_settings(crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG)


@pytest.mark.basic
def test_missing_factor_from_hierarchy_info_throws_exception():
    hierarchy_json = create_test_hierarchy_json([
        FakeHierarchyItem(FACTOR_NAMES_TRANSLATION[FactorType.RELEASE_DATE], True, True)
    ])
    crunched_df = create_simple_crunched_df()

    with pytest.raises(DataTransformationError):
        _ = create_default_plot_settings(crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG)


@pytest.mark.basic
def test_less_than_100_structures_in_one_bucket_throws_exception():
    hierarchy_json = create_test_hierarchy_json_with_release_date_and_resolution()
    too_small_crunched_df = pd.DataFrame({
        FactorType.RELEASE_DATE.value: [1999, 2020], FactorType.RESOLUTION.value: [1, 2]
    })

    with pytest.raises(DataTransformationError):
        _ = create_default_plot_settings(too_small_crunched_df, FACTOR_NAMES_TRANSLATION, hierarchy_json, TEST_CONFIG)


@pytest.mark.basic
def test_default_plot_data_instance_serializes_as_expected():
    # arrange
    plot_settings_item = DefaultPlotSettingsItem(
        bucked_width=Decimal(0.1),
        x_factor_familiar_name="dummy name",
        x_limit_lower=Decimal(3.5),
        x_limit_upper=Decimal(4.5),
    )
    expected_result_json = {
        "BucketWidth": 0.1,
        "Factor": "dummy name",
        "XlimitLower": 3.5,
        "XlimitUpper": 4.5,
    }
    # act
    item_as_dictionary = plot_settings_item.to_dict()
    # assert
    assert json.dumps(expected_result_json, sort_keys=True) == json.dumps(item_as_dictionary, sort_keys=True)
