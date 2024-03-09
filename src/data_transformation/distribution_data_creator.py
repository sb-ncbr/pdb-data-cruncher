import logging
from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

import pandas as pd

from src.exception import DataTransformationError
from src.models import FactorType
from src.models.transformed import DistributionData, DistributionDataBucket
from src.utils import round_relative


class Direction(Enum):
    """
    Direction of the neighbour for determining which neighbour should be merged.
    """

    LEFT = 0
    RIGHT = 1


@dataclass(slots=True)
class WorkingBucket:
    """
    Structure representing distribution data bucket in making.
    """

    bucket_id: int
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

    def __eq__(self, other):
        """
        Compare buckets based on the bucket_id alone.
        :param other: The other bucket to compare.
        :return: True if the bucket id is the same, false otherwise.
        """
        return self.bucket_id == other.bucket_id


def create_distribution_data(crunched_df: pd.DataFrame, factor_types: dict[FactorType, str]) -> list[DistributionData]:
    """
    Create distribution data for all the factors.
    :param crunched_df: Dataframe with loaded crunched csv.
    :param factor_types: List of factor types to create distribution data for.
    :return: List of created distribution data.
    """
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
                "[%s] failed to create distribution data. KeyError: %s", factor_type.value, str(ex)
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
    """
    Create distribution data for one factor type.
    :param factor_type: Factor type.
    :param factor_familiar_name: Familiar name for the factor type.
    :param crunched_series: Pandas series representing only the one relevant column from crunched csv.
    :return: Created distribution data for the factor.
    """
    distribution_data = DistributionData(factor_type, factor_familiar_name)
    # create buckets sorted by structure count
    working_buckets = [
        WorkingBucket(bucket_id=i, left=x_value, right=x_value, count=count)
        for i, (x_value, count)
        in enumerate(crunched_series.value_counts().sort_index().items())
    ]
    _load_bucket_neighbours(working_buckets)
    working_buckets = _merge_buckets(working_buckets)
    distribution_data.buckets = _create_final_data_buckets(working_buckets)
    return distribution_data


def _load_bucket_neighbours(buckets: list[WorkingBucket]) -> None:
    """
    Adds reference to left and right neighbouring bucket, according to the order as they are passed into the function.
    :param buckets: Sorted buckets.
    """
    for i, bucket in enumerate(buckets):
        if i != 0:
            bucket.bucket_on_left = buckets[i-1]
        if i + 1 != len(buckets):
            bucket.bucket_on_right = buckets[i+1]


def _merge_buckets(buckets: list[WorkingBucket], max_target_buckets: int = 200) -> list[WorkingBucket]:
    """
    Merge given buckets together until there are at most max_target_buckets (default 200) buckets.
    :param buckets: List of working buckets to merge.
    :param max_target_buckets: The limit of buckets, will merge them until there is at most that much buckets.
    :return:
    """
    if len(buckets) <= max_target_buckets:
        return buckets

    buckets_by_counts = {}
    for bucket in buckets:
        _sort_bucket_into_buckets_by_counts(bucket, buckets_by_counts)

    # create dict where structure count - the buckets, and use that to sort throught the buckets
    min_bucket_size = min(buckets_by_counts)
    while _count_buckets(buckets_by_counts) > max_target_buckets:
        if min_bucket_size not in buckets_by_counts:  # the value list was already emptied by removing merge bucket
            min_bucket_size = min(buckets_by_counts)
        if len(buckets_by_counts[min_bucket_size]) == 0:
            buckets_by_counts.pop(min_bucket_size)  # remove the empty counts from the dictionary
            min_bucket_size = min(buckets_by_counts)  # load new minimal count
        smallest_bucket = buckets_by_counts[min_bucket_size].pop()  # get first item from the list of smallest buckets
        _merge_bucket_into_its_smaller_neighbour(smallest_bucket, buckets_by_counts)

    return sorted(
        [bucket for bucket_list in buckets_by_counts.values() for bucket in bucket_list], key=lambda b: b.left
    )


def _count_buckets(buckets_by_counts: dict[int, list[WorkingBucket]]) -> int:
    """
    Count all buckets in sorted dictionary.
    :param buckets_by_counts: Dictionary with buckets sorted by their count.
    :return: Total number of buckets.
    """
    return sum([len(bucket_list) for bucket_list in buckets_by_counts.values()])


def _sort_bucket_into_buckets_by_counts(
    bucket: WorkingBucket, buckets_by_counts: dict[int, list[WorkingBucket]]
) -> None:
    """
    Sort bucket into the dictionary based on their structure count.
    :param bucket: Bucket to insert into the buckets by counts dictionary.
    :param buckets_by_counts: Dictionary with keys structure counts, and values list of buckets that have
    that structure count.
    """
    if bucket.count in buckets_by_counts:
        buckets_by_counts[bucket.count].append(bucket)
    else:
        buckets_by_counts[bucket.count] = [bucket]


def _merge_bucket_into_its_smaller_neighbour(
    smallest_bucket: WorkingBucket, buckets_by_counts: dict[int, list[WorkingBucket]]
) -> None:
    """
    Merge given bucket into one of its neighbours (the one with smaller structure count). Adjust the structure count
    and right/left boundaries of the neighbouring bucket, as well as its new neighbour values. Moves the new merged
    bucket into appropriate place in buckets by counts dictionary, and removes the original list if it used to be
    the last value there.
    :param smallest_bucket: Small bucket to merge into its neighbour.
    :param buckets_by_counts: Dictionary with keys structure counts, and values list of buckets that have such
    structure count.
    """
    if smallest_bucket.smaller_neighbour_direction() == Direction.LEFT:
        merged_bucket = smallest_bucket.bucket_on_left
        merged_bucket_count_before = merged_bucket.count
        merged_bucket.count += smallest_bucket.count
        merged_bucket.right = smallest_bucket.right
    else:  # smaller neighbour is on right
        merged_bucket = smallest_bucket.bucket_on_right
        merged_bucket_count_before = merged_bucket.count
        merged_bucket.count += smallest_bucket.count
        merged_bucket.left = smallest_bucket.left

    _point_neighbours_to_each_other(smallest_bucket)
    # remove the new merged bucket from buckets_by_counts
    buckets_by_counts[merged_bucket_count_before].remove(merged_bucket)
    if len(buckets_by_counts[merged_bucket_count_before]) == 0:  # if the merged bucket was the last with such count
        buckets_by_counts.pop(merged_bucket_count_before)  # remove the empty list
    _sort_bucket_into_buckets_by_counts(merged_bucket, buckets_by_counts)


def _point_neighbours_to_each_other(bucket_to_remove: WorkingBucket) -> None:
    """
    Points the left and right neighbour of bucket that is to be removed to each other, skipping the bucket to be
    removed.
    :param bucket_to_remove: Bucket which neighbours should point to each other instead of to this bucket.
    """
    if bucket_to_remove.bucket_on_left:
        bucket_to_remove.bucket_on_left.bucket_on_right = bucket_to_remove.bucket_on_right
    if bucket_to_remove.bucket_on_right:
        bucket_to_remove.bucket_on_right.bucket_on_left = bucket_to_remove.bucket_on_left


def _create_final_data_buckets(working_buckets: list[WorkingBucket]) -> list[DistributionDataBucket]:
    """
    Process working buckets into final DistributionDataBuckets.
    :param working_buckets: List of working buckets.
    :return: List of distribution data buckets with desired information.
    """
    final_buckets = []
    for working_bucket in working_buckets:
        final_buckets.append(DistributionDataBucket(
            x_from=working_bucket.left,
            x_to=working_bucket.right,
            is_interval=(working_bucket.left != working_bucket.right),
            structure_count=working_bucket.count,
        ))
    return final_buckets
