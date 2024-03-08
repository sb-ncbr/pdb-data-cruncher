import logging
from typing import Union, Optional
from enum import Enum

import pandas as pd
from dataclasses import dataclass

from src.models import FactorType
from src.models.transformed import DistributionData, DistributionDataBucket
from src.utils import round_relative
from src.exception import DataTransformationError


class Direction(Enum):
    LEFT = 0
    RIGHT = 1


@dataclass(slots=True)
class WorkingBucket:
    left: Union[float, int]
    right: Union[float, int]
    count: int
    bucket_on_left: Optional['WorkingBucket'] = None
    bucket_on_right: Optional['WorkingBucket'] = None

    def smaller_neighbour_direction(self) -> Direction:
        """
        Get one of the neighbours that is smaller.
        :return: The smaller neighbouring bucket.
        :raises DataTransformationError: If both neighbouring buckets are missing.
        """
        if self.bucket_on_left is None and self.bucket_on_right is None:
            raise DataTransformationError(f"Working bucket [{self.left},{self.right}] has no neighbours.")
        if self.bucket_on_right is None:
            return Direction.LEFT
        if self.bucket_on_left is None:
            return Direction.RIGHT
        if self.bucket_on_left.count < self.bucket_on_right.count:
            return Direction.LEFT
        return Direction.RIGHT


def create_distribution_data(crunched_df: pd.DataFrame, factor_types: dict[FactorType, str]) -> list[DistributionData]:
    distribution_data_list = []
    failed_factors_count = 0

    for factor_type, factor_familiar_name in factor_types.items():
        try:
            factor_crunched_series = crunched_df[factor_type.value]
            factor_crunched_series = factor_crunched_series.dropna().apply(round_relative)
            distribution_data_list.append(_create_distribution_data_for_factor(
                factor_type, factor_familiar_name, factor_crunched_series.dropna()
            ))
        except KeyError as ex:
            logging.error(
                "[%] failed to create distribution data. KeyError: %s", factor_type.value, str(ex)
            )
            failed_factors_count += 1

    if failed_factors_count > 0:
        raise DataTransformationError(
            f"Distribution data creation failed. {failed_factors_count} factors could not be processed."
        )

    return distribution_data_list


def _create_distribution_data_for_factor(
        factor_type: FactorType, factor_familiar_name: str, crunched_series: pd.Series
) -> DistributionData:
    distribution_data = DistributionData(factor_type, factor_familiar_name)
    # create buckets sorted by structure count
    working_buckets = [
        WorkingBucket(left=x_value, right=x_value, count=count)
        for x_value, count
        in crunched_series.value_counts().sort_index().items()
    ]
    _load_bucket_neighbours(working_buckets)
    _merge_buckets(working_buckets)
    distribution_data.buckets = _create_final_data_buckets(working_buckets)
    return distribution_data


def _load_bucket_neighbours(buckets: list[WorkingBucket]) -> None:
    for i, bucket in enumerate(buckets):
        if i != 0:
            bucket.bucket_on_left = buckets[i-1]
        if i + 1 != len(buckets):
            bucket.bucket_on_right = buckets[i+1]


def _merge_buckets(buckets: list[WorkingBucket], max_target_buckets: int = 200) -> None:
    while len(buckets) > max_target_buckets:
        smallest_bucket = min(buckets, key=lambda bucket: bucket.count)
        buckets.remove(smallest_bucket)  # remove bucket form bucket list
        if smallest_bucket.smaller_neighbour_direction() == Direction.LEFT:
            smallest_bucket.bucket_on_left.count += smallest_bucket.count
            smallest_bucket.bucket_on_left.right = smallest_bucket.right
            _point_neighbours_to_each_other(smallest_bucket)
        else:  # smaller neighbour is on right
            smallest_bucket.bucket_on_right.count += smallest_bucket.count
            smallest_bucket.bucket_on_right.left = smallest_bucket.left
            _point_neighbours_to_each_other(smallest_bucket)


def _point_neighbours_to_each_other(bucket_to_remove: WorkingBucket) -> None:
    if bucket_to_remove.bucket_on_left:
        bucket_to_remove.bucket_on_left.bucket_on_right = bucket_to_remove.bucket_on_right
    if bucket_to_remove.bucket_on_right:
        bucket_to_remove.bucket_on_right.bucket_on_left = bucket_to_remove.bucket_on_left


def _create_final_data_buckets(working_buckets: list[WorkingBucket]) -> list[DistributionDataBucket]:
    final_buckets = []
    for working_bucket in working_buckets:
        final_buckets.append(DistributionDataBucket(
            x_from=working_bucket.left,
            x_to=working_bucket.right,
            is_interval=(working_bucket.left != working_bucket.right),
            structure_count=working_bucket.count,
        ))
    return final_buckets
