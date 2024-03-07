import pytest
import json
from unittest import mock

from src.data_transformation.default_plot_data_creator import create_default_plot_data
from src.models import FactorType
from src.models.transformed import DefaultPlotData, DefaultPlotBucket, FactorPair
from src.exception import DataTransformationError


FAMILIAR_NAMES_TRANSLATION = {
    FactorType.RELEASE_DATE.value: "year of release",
    FactorType.RESOLUTION.value: "structure resolution [A]",
}


def create_test_simple_crunched_csv() -> str:
    content = f"PDB ID;{FactorType.RELEASE_DATE.value};{FactorType.RESOLUTION.value}\n"
    for _ in range(100):
        content += f"xxxx;{1990};1.0\nxxxx;{2000};2.0\nxxxx;{2015};3.0\n"
    return content


def create_test_empty_buckets_crunched_csv() -> str:
    content = f"PDB ID;{FactorType.RELEASE_DATE.value};{FactorType.RESOLUTION.value}\n"
    for _ in range(100):
        content += f"xxxx;{1990};1.0\nxxxx;{1995};1.0\nxxxx;{1998};1.0\n"  # 300 into the first test iterval
        content += f"xxxx;{2012};3.0\nxxxx;{2015};3.0\n"  # 200 into the third test interval (second is empty)
    return content


def create_test_joining_buckets_crunched_csv() -> str:
    content = f"PDB ID;{FactorType.RELEASE_DATE.value};{FactorType.RESOLUTION.value}\n"
    for _ in range(100):
        content += f"xxxx;{1990};1.0\nxxxx;{1995};1.0\nxxxx;{1998};1.0\n"  # 300 into the first test iterval
        content += f"xxxx;{2012};3.0\nxxxx;{2015};3.0\n"  # 200 into the third test interval

    for _ in range(80):
        content += f"xxxx;{2005};2.0\n"  # only 80 into the second interval

    return content


def create_test_x_limits(factor_type, values):
    content = f";{factor_type.value}\n"
    i = 1
    for value in values:
        content += f"{i};{value}\n"
        i += 1
    while i < 102:  # to emulate usual source file
        content += f"{i};NA\n"
        i += 1
    return content


def plot_data_mock_open(filename, *args, **kwargs):
    if filename == "test_simple_crunched.csv":
        content = create_test_simple_crunched_csv()
    elif filename == "test_joining_buckets_crunched.csv":
        content = create_test_joining_buckets_crunched_csv()
    elif filename == "test_empty_buckets_crunched.csv":
        content = create_test_empty_buckets_crunched_csv()
    elif filename == "test_simple_x_limits.csv":
        content = create_test_x_limits(FactorType.RELEASE_DATE, [-0.01, 2000, 2010])
    elif filename == "test_joining_buckets_x_limits.csv":
        content = create_test_x_limits(FactorType.RELEASE_DATE, [-0.01, 2000, 2010, 2020])
    elif filename == "test_empty_buckets_x_limits.csv":
        content = create_test_x_limits(FactorType.RELEASE_DATE, [-0.01, 2000, 2010, 2020])
    elif filename == "wrong_x_limits.csv":
        content = create_test_x_limits(FactorType.RELEASE_DATE, [-0.01, 2010, 2000])
    else:
        raise FileNotFoundError("Mock file not found error")

    file_object = mock.mock_open(read_data=content).return_value
    file_object.__iter__.return_vlaue = content.splitlines(True)
    return file_object


@mock.patch("builtins.open", new=plot_data_mock_open)
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

    # act
    plot_data_list = create_default_plot_data(
        "test_simple_crunched.csv", "test_simple_x_limits.csv", factor_pairs, FAMILIAR_NAMES_TRANSLATION
    )

    # assert
    assert plot_data_list
    assert len(plot_data_list) == 1
    plot_data = plot_data_list[0]
    plot_data_string = json.dumps(plot_data.to_dict(), sort_keys=True)
    expected_result_string = json.dumps(expected_result, sort_keys=True)
    assert plot_data_string == expected_result_string


# joining buckets works as expected
@mock.patch("builtins.open", new=plot_data_mock_open)
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

    # act
    plot_data_list = create_default_plot_data(
        "test_joining_buckets_crunched.csv",
        "test_joining_buckets_x_limits.csv",
        factor_pairs,
        FAMILIAR_NAMES_TRANSLATION,
    )

    # assert
    assert plot_data_list
    assert len(plot_data_list) == 1
    plot_data = plot_data_list[0]
    plot_data_string = json.dumps(plot_data.to_dict(), sort_keys=True)
    expected_result_string = json.dumps(expected_result, sort_keys=True)
    assert plot_data_string == expected_result_string


@mock.patch("builtins.open", new=plot_data_mock_open)
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

    # act
    plot_data_list = create_default_plot_data(
        "test_empty_buckets_crunched.csv", "test_empty_buckets_x_limits.csv", factor_pairs, FAMILIAR_NAMES_TRANSLATION
    )

    # assert
    assert plot_data_list
    assert len(plot_data_list) == 1
    plot_data = plot_data_list[0]
    plot_data_string = json.dumps(plot_data.to_dict(), sort_keys=True)
    expected_result_string = json.dumps(expected_result, sort_keys=True)
    assert plot_data_string == expected_result_string


@mock.patch("builtins.open", new=plot_data_mock_open)
@pytest.mark.basic
def test_creation_fails_on_invalid_x_limits():
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.RESOLUTION)]

    with pytest.raises(DataTransformationError) as e_info:
        _ = create_default_plot_data(
            "test_simple_crunched.csv", "wrong_x_limits.csv", factor_pairs, FAMILIAR_NAMES_TRANSLATION
        )


@mock.patch("builtins.open", new=plot_data_mock_open)
@pytest.mark.basic
def test_creation_fails_on_missing_csv_column():
    factor_pairs = [FactorPair(FactorType.RELEASE_DATE, FactorType.AA_COUNT)]  # AA_COUNT will not be in mocked csv

    with pytest.raises(DataTransformationError) as e_info:
        _ = create_default_plot_data(
            "test_simple_crunched.csv", "test_simple_x_limits.csv", factor_pairs, FAMILIAR_NAMES_TRANSLATION
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
