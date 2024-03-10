import pandas as pd
import pytest
import json

from src.data_transformation.distribution_data_creator import create_distribution_data
from src.models import FactorType
from src.models.transformed import DistributionData, DistributionDataBucket
from src.exception import DataTransformationError


FACTOR_TYPE_TRANSLATIONS = {
    FactorType.RELEASE_DATE: "year of release",
    FactorType.RESOLUTION: "structure resolution [A]",
}


@pytest.mark.basic
def test_small_distribution_data_creation():
    factor_types = [FactorType.RELEASE_DATE]
    crunched_df = pd.DataFrame({FactorType.RELEASE_DATE.value: [2020, 2010, 2010, 2010, 2015, 2015]})
    expected_result = DistributionData(
        factor_type=FactorType.RELEASE_DATE,
        factor_familiar_name="year of release",
        buckets=[
            DistributionDataBucket(
                x_from=2010,
                x_to=2010,
                is_interval=False,
                structure_count=3,
            ),
            DistributionDataBucket(
                x_from=2015,
                x_to=2015,
                is_interval=False,
                structure_count=2,
            ),
            DistributionDataBucket(
                x_from=2020,
                x_to=2020,
                is_interval=False,
                structure_count=1,
            )
        ]
    )

    actual_result = create_distribution_data(crunched_df, factor_types, FACTOR_TYPE_TRANSLATIONS)[0]

    assert actual_result == expected_result


@pytest.mark.basic
def test_distribution_data_creation_with_bucket_merging():
    # arrange
    factor_types = [FactorType.RESOLUTION]
    expected_result = DistributionData(
        factor_type=FactorType.RESOLUTION, factor_familiar_name="structure resolution [A]"
    )
    crunched_df_data = []
    for i in range(198):
        # load 0.00, 0.01 ... 1.98 into the dataframe, each 10 times
        resolution_value = i/100
        crunched_df_data.extend([resolution_value for _ in range(10)])
        # such values will be expected in the result unmerged
        expected_result.buckets.append(DistributionDataBucket(
            x_from=resolution_value,
            x_to=resolution_value,
            is_interval=False,
            structure_count=10,
        ))

    # add value 4.0 with count 2 that will be expected to be merged with the smallest value
    crunched_df_data.append(4.0)
    crunched_df_data.append(4.0)
    expected_result.buckets.append(DistributionDataBucket(
        x_from=4.0,
        x_to=5.0,
        is_interval=True,
        structure_count=3,
    ))
    # add value 5.0 with count 1 that will be expected to merge with its smaller neighbour
    crunched_df_data.append(5.0)
    # add value 6.0 with count 3 that will be expected to stay unchanged
    for _ in range(3):
        crunched_df_data.append(6.0)
    expected_result.buckets.append(DistributionDataBucket(
        x_from=6.0,
        x_to=6.0,
        is_interval=False,
        structure_count=3,
    ))
    # create dataframe from prepared data
    crunched_df = pd.DataFrame({FactorType.RESOLUTION.value: crunched_df_data})

    # act
    actual_result = create_distribution_data(crunched_df, factor_types, FACTOR_TYPE_TRANSLATIONS)[0]

    # assert
    assert actual_result == expected_result


@pytest.mark.basic
def test_creation_fails_on_missing_crunched_column():
    factor_types = [FactorType.RESOLUTION]
    with pytest.raises(DataTransformationError):
        _ = create_distribution_data(pd.DataFrame(), factor_types, FACTOR_TYPE_TRANSLATIONS)


@pytest.mark.basic
def test_distribution_data_serialization():
    distribution_data = DistributionData(
        factor_type=FactorType.RELEASE_DATE,
        factor_familiar_name="year of release",
        buckets=[
            DistributionDataBucket(
                x_from=2010,
                x_to=2010,
                is_interval=False,
                structure_count=3,
            ),
            DistributionDataBucket(
                x_from=2014,
                x_to=2016,
                is_interval=True,
                structure_count=2,
            ),
            DistributionDataBucket(
                x_from=2020,
                x_to=2020,
                is_interval=False,
                structure_count=1,
            )
        ]
    )

    expected_result = {
        "Bins": [
            {
                "Xfrom": "2010",
                "XisInterval": False,
                "Xto": "2010",
                "YstructureCount": "3",
            },
            {
                "Xfrom": "2014",
                "XisInterval": True,
                "Xto": "2016",
                "YstructureCount": "2",
            },
            {
                "Xfrom": "2020",
                "XisInterval": False,
                "Xto": "2020",
                "YstructureCount": "1",
            },
        ],
        "Factor": "year of release",
    }

    distribution_data_json_string = json.dumps(distribution_data.to_dict(), sort_keys=True)
    expected_result_json_string = json.dumps(expected_result, sort_keys=True)

    assert distribution_data_json_string == expected_result_json_string
