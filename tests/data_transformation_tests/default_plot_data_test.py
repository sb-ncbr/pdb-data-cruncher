import pandas as pd
import pytest
import json

from src.data_transformation.default_plot_data_creator import create_default_plot_data
from src.models import FactorType
from src.models.transformed import DefaultPlotData, DefaultPlotBucket, FactorPair
from src.exception import DataTransformationError


FAMILIAR_NAMES_TRANSLATION = {
    FactorType.RELEASE_DATE.value: "year of release",
    FactorType.RESOLUTION.value: "structure resolution [A]",
}


def create_simple_crunched_df() -> pd.DataFrame:
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    for _ in range(100):
        dummy_pdb_ids.extend(["xxxx", "xxxx", "xxxx"])
        release_date_values.extend([1990, 2000, 2015])
        resolution_values.extend([1.0, 2.0, 3.0])

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values
    })


def create_crunched_df_for_empty_buckets() -> pd.DataFrame:
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    for _ in range(100):
        dummy_pdb_ids.extend(["xxxx", "xxxx", "xxxx", "xxxx", "xxxx"])
        release_date_values.extend([1990, 1995, 1998, 2012, 2015])  # 300 into first interval, 200 into other
        resolution_values.extend([1.0, 1.0, 1.0, 3.0, 3.0])

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values
    })


def create_crunched_df_for_joining_buckets() -> pd.DataFrame:
    dummy_pdb_ids = []
    release_date_values = []
    resolution_values = []
    for _ in range(100):
        dummy_pdb_ids.extend(["xxxx", "xxxx", "xxxx", "xxxx", "xxxx"])
        release_date_values.extend([1990, 1995, 1998, 2012, 2015])  # 300 into first interval, 200 into other
        resolution_values.extend([1.0, 1.0, 1.0, 3.0, 3.0])
    for _ in range(80):  # add only 80 values into the range, so they need to get merged
        dummy_pdb_ids.append("xxxx")
        release_date_values.append(2005)
        resolution_values.append(2.0)

    return pd.DataFrame({
        "PDB ID": dummy_pdb_ids,
        FactorType.RELEASE_DATE.value: release_date_values,
        FactorType.RESOLUTION.value: resolution_values
    })


@pytest.mark.basic
def test_simple_default_plot_data_creation_works():
    # arrange
    expected_result = {
        "GraphBuckets": [
            {
                "BucketOrdinalNumber": "1",
                "StructureCountInBucket": "100",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "1990",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "2000"},
                "YfactorAverage": "1.0",
                "YfactorHighQuartile": "1.0",
                "YfactorLowQuartile": "1.0",
                "YfactorMaximum": "1.0",
                "YfactorMedian": "1.0",
                "YfactorMinimum": "1.0",
            },
            {
                "BucketOrdinalNumber": "2",
                "StructureCountInBucket": "100",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "2000",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "2010"},
                "YfactorAverage": "2.0",
                "YfactorHighQuartile": "2.0",
                "YfactorLowQuartile": "2.0",
                "YfactorMaximum": "2.0",
                "YfactorMedian": "2.0",
                "YfactorMinimum": "2.0",
            },
            {
                "BucketOrdinalNumber": "3",
                "StructureCountInBucket": "100",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "2010",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": False, "XfactorToValue": "2015"},
                "YfactorAverage": "3.0",
                "YfactorHighQuartile": "3.0",
                "YfactorLowQuartile": "3.0",
                "YfactorMaximum": "3.0",
                "YfactorMedian": "3.0",
                "YfactorMinimum": "3.0",
            },
        ],
        "StructureCount": "300",
        "XfactorGlobalMaximum": "2015",
        "XfactorGlobalMinimum": "1990",
        "XfactorName": "year of release",
        "YfactorGlobalMaximum": "3.0",
        "YfactorGlobalMinimum": "1.0",
        "YfactorName": "structure resolution [A]",
    }
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.RESOLUTION)]

    crunched_df = create_simple_crunched_df()
    x_bucket_limits = pd.DataFrame({FactorType.RELEASE_DATE.value: [-0.01, 2000, 2010]})

    # act
    plot_data_list = create_default_plot_data(
        crunched_df, x_bucket_limits, factor_pairs, FAMILIAR_NAMES_TRANSLATION
    )

    # assert
    assert plot_data_list
    assert len(plot_data_list) == 1
    plot_data = plot_data_list[0]
    plot_data_string = json.dumps(plot_data.to_dict(), sort_keys=True)
    expected_result_string = json.dumps(expected_result, sort_keys=True)
    assert plot_data_string == expected_result_string


@pytest.mark.basic
def test_small_buckets_get_merged():
    # arrange
    expected_result = {
        "GraphBuckets": [
            {
                "BucketOrdinalNumber": "1",
                "StructureCountInBucket": "300",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "1990",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "2000"},
                "YfactorAverage": "1.0",
                "YfactorHighQuartile": "1.0",
                "YfactorLowQuartile": "1.0",
                "YfactorMaximum": "1.0",
                "YfactorMedian": "1.0",
                "YfactorMinimum": "1.0",
            },
            {
                "BucketOrdinalNumber": "2",
                "StructureCountInBucket": "280",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "2000",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "2020"},
                "YfactorAverage": "2.71",
                "YfactorHighQuartile": "3.0",
                "YfactorLowQuartile": "2.0",
                "YfactorMaximum": "3.0",
                "YfactorMedian": "3.0",
                "YfactorMinimum": "2.0",
            },
        ],
        "StructureCount": "580",
        "XfactorGlobalMaximum": "2015",
        "XfactorGlobalMinimum": "1990",
        "XfactorName": "year of release",
        "YfactorGlobalMaximum": "3.0",
        "YfactorGlobalMinimum": "1.0",
        "YfactorName": "structure resolution [A]",
    }
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.RESOLUTION)]

    crunched_df = create_crunched_df_for_joining_buckets()
    x_bucket_limits = pd.DataFrame({FactorType.RELEASE_DATE.value: [-0.01, 2000, 2010, 2020]})

    # act
    plot_data_list = create_default_plot_data(
        crunched_df, x_bucket_limits, factor_pairs, FAMILIAR_NAMES_TRANSLATION
    )

    # assert
    assert plot_data_list
    assert len(plot_data_list) == 1
    plot_data = plot_data_list[0]
    plot_data_string = json.dumps(plot_data.to_dict(), sort_keys=True)
    expected_result_string = json.dumps(expected_result, sort_keys=True)
    assert plot_data_string == expected_result_string


@pytest.mark.basic
def test_empty_buckets_get_merged():
    # arrange
    expected_result = {
        "GraphBuckets": [
            {
                "BucketOrdinalNumber": "1",
                "StructureCountInBucket": "300",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "1990",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "2000"},
                "YfactorAverage": "1.0",
                "YfactorHighQuartile": "1.0",
                "YfactorLowQuartile": "1.0",
                "YfactorMaximum": "1.0",
                "YfactorMedian": "1.0",
                "YfactorMinimum": "1.0",
            },
            {
                "BucketOrdinalNumber": "2",
                "StructureCountInBucket": "200",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "2000",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "2020"},
                "YfactorAverage": "3.0",
                "YfactorHighQuartile": "3.0",
                "YfactorLowQuartile": "3.0",
                "YfactorMaximum": "3.0",
                "YfactorMedian": "3.0",
                "YfactorMinimum": "3.0",
            },
        ],
        "StructureCount": "500",
        "XfactorGlobalMaximum": "2015",
        "XfactorGlobalMinimum": "1990",
        "XfactorName": "year of release",
        "YfactorGlobalMaximum": "3.0",
        "YfactorGlobalMinimum": "1.0",
        "YfactorName": "structure resolution [A]",
    }
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.RESOLUTION)]
    crunched_df = create_crunched_df_for_empty_buckets()
    x_bucket_limits = pd.DataFrame({FactorType.RELEASE_DATE.value: [-0.01, 2000, 2010, 2020]})

    # act
    plot_data_list = create_default_plot_data(
        crunched_df, x_bucket_limits, factor_pairs, FAMILIAR_NAMES_TRANSLATION
    )

    # assert
    assert plot_data_list
    assert len(plot_data_list) == 1
    plot_data = plot_data_list[0]
    plot_data_string = json.dumps(plot_data.to_dict(), sort_keys=True)
    expected_result_string = json.dumps(expected_result, sort_keys=True)
    assert plot_data_string == expected_result_string


@pytest.mark.basic
def test_creation_fails_on_invalid_x_limits():
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.RESOLUTION)]
    crunched_df = create_simple_crunched_df()
    wrong_x_bucket_limits = pd.DataFrame({FactorType.RELEASE_DATE.value: [2000, 2020, 2010]})

    with pytest.raises(DataTransformationError):
        _ = create_default_plot_data(
            crunched_df, wrong_x_bucket_limits, factor_pairs, FAMILIAR_NAMES_TRANSLATION
        )


@pytest.mark.basic
def test_creation_fails_on_missing_csv_column():
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.AA_COUNT)]  # AA_COUNT is not in test crunched df
    crunched_df = create_simple_crunched_df()
    x_bucket_limits = pd.DataFrame({FactorType.RELEASE_DATE.value: [-0.01, 2000, 2010, 2020]})

    with pytest.raises(DataTransformationError):
        _ = create_default_plot_data(
            crunched_df, x_bucket_limits, factor_pairs, FAMILIAR_NAMES_TRANSLATION
        )


@pytest.mark.basic
def test_default_plot_data_instance_serializes_as_expected():
    plot_data = DefaultPlotData(
        x_factor=FactorType.RELEASE_DATE,
        y_factor=FactorType.RESOLUTION,
        x_factor_familiar_name="year of release",
        y_factor_familiar_name="structure resolution [A]",
        x_factor_global_maximum=2024,
        x_factor_global_minimum=1976,
        y_factor_global_maximum=70.0,
        y_factor_global_minimum=0.48,
        structure_count=200420,
    )
    plot_bucket = DefaultPlotBucket(1)
    plot_bucket.structure_count = 1465
    plot_bucket.x_factor_from.open_interval = False
    plot_bucket.x_factor_from.value = 1976
    plot_bucket.x_factor_to.open_interval = True
    plot_bucket.x_factor_to.value = 1994.0  # to check rounding works correctly (because it is year)
    plot_bucket.y_factor_average = 2.1426  # to check rounding works correctly (because only 3 significant places)
    plot_bucket.y_factor_median = 2.0
    plot_bucket.y_factor_minimum = 0.9
    plot_bucket.y_factor_maximum = 15.0
    plot_bucket.y_factor_low_quartile = 1.8
    plot_bucket.y_factor_high_quartile = 2.5
    plot_data.graph_buckets.append(plot_bucket)

    expected_result = {
        "GraphBuckets": [
            {
                "BucketOrdinalNumber": "1",
                "StructureCountInBucket": "1465",
                "XfactorFrom": {
                    "XfactorFromIsInfinity": False,
                    "XfactorFromOpenInterval": False,
                    "XfactorFromValue": "1976",
                },
                "XfactorTo": {"XfactorToIsInfinity": False, "XfactorToOpenInterval": True, "XfactorToValue": "1994"},
                "YfactorAverage": "2.14",
                "YfactorHighQuartile": "2.5",
                "YfactorLowQuartile": "1.8",
                "YfactorMaximum": "15.0",
                "YfactorMedian": "2.0",
                "YfactorMinimum": "0.9",
            },
        ],
        "StructureCount": "200420",
        "XfactorGlobalMaximum": "2024",
        "XfactorGlobalMinimum": "1976",
        "XfactorName": "year of release",
        "YfactorGlobalMaximum": "70.0",
        "YfactorGlobalMinimum": "0.48",
        "YfactorName": "structure resolution [A]",
    }
    actual_result = plot_data.to_dict()
    actual_result_json_string = json.dumps(actual_result, sort_keys=True)
    expected_result_json_string = json.dumps(expected_result, sort_keys=True)

    # assert
    assert actual_result_json_string == expected_result_json_string
