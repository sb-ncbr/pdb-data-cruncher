import logging
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from src.models.transformed import DefaultPlotBucket, DefaultPlotData, FactorPair
from src.models import FactorType
from src.exception import ParsingError, DataTransformationError


@dataclass
class WorkingBucket:
    """
    Represents data about one bucket as they are extracted, before they are processed into a DefaultPlotBucket.
    """
    interval: pd.Interval
    factor_pair: FactorPair
    structure_count: int = 0
    data: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def x_factor_data(self) -> pd.Series:
        """
        Data series with values of factor X.
        """
        return self.data[self.factor_pair.x.value]

    @property
    def y_factor_data(self) -> pd.Series:
        """
        Data series with values of factor Y.
        """
        return self.data[self.factor_pair.y.value]


def create_default_plot_data(
        crunched_csv_filepath: str,
        x_factor_bucket_limits_filepath: str,
        factor_pairs: list[FactorPair],
        familiar_names_translation: dict[str, str]
) -> list[DefaultPlotData]:
    """
    Create default plot data for all given factor pairs.
    :param crunched_csv_filepath: Path to a cvs file with crunched data.
    :param x_factor_bucket_limits_filepath: Path to a csv file with values for bucket intervals for each factor.
    :param factor_pairs: List of factor pairs (factors on x and y)
    :param familiar_names_translation: Dictionary with translations from factor name into familiar name.
    :return: List of default plot data.
    :raises DataTransformationError: Upon encountering unrecoverable error.
    """
    crunched_df = _load_csv_as_dataframe(crunched_csv_filepath)
    bucket_limits_df = _load_csv_as_dataframe(x_factor_bucket_limits_filepath)

    default_plot_data = []
    failed_factor_pairs_count = 0

    for factor_pair in factor_pairs:
        logging.debug(
            "[%s+%s] Processing default plot data for pair", factor_pair.x.value, factor_pair.y.value
        )

        try:
            factor_pair_crunched_df = crunched_df[[factor_pair.x.value, factor_pair.y.value]].dropna()
            x_bucket_limit_series = bucket_limits_df[factor_pair.x.value].dropna()
            _add_inf_boundaries_to_bucket_timits(x_bucket_limit_series)
            x_bucket_intervals = pd.IntervalIndex.from_breaks(x_bucket_limit_series, closed="left")
            single_plot_data = _create_default_plot_data_for_factor_pair(
                factor_pair,
                factor_pair_crunched_df,
                x_bucket_intervals,
                familiar_names_translation
            )
            default_plot_data.append(single_plot_data)
        except (KeyError, ValueError) as ex:
            logging.error(
                "[%s+%s] failed to create default data. %s: %s",
                factor_pair.x.value,
                factor_pair.y.value,
                ex.__class__.__name__,
                str(ex)
            )
            failed_factor_pairs_count += 1

    if failed_factor_pairs_count > 0:
        raise DataTransformationError(
            f"Default plot data creation failed. {failed_factor_pairs_count} factor pairs could not be extracted"
        )

    return default_plot_data


def _create_default_plot_data_for_factor_pair(
    factor_pair: FactorPair,
    crunched_df: pd.DataFrame,
    x_bucket_intervals: pd.IntervalIndex,
    familiar_names_translation: dict[str, str]
) -> DefaultPlotData:
    """
    Create default plot data for given factor pair.
    :param factor_pair: Factor pair to create plot data for.
    :param crunched_df: Dataframe with crunched csv data.
    :param x_bucket_intervals: Intervals representing bucket limits into which to sort the data.
    :param familiar_names_translation: Dictionary with translations from factor name into familiar name.
    :return: Instance of DefaultPlotData loaded with collected data.
    """
    default_plot_data = DefaultPlotData(
        x_factor=factor_pair.x,
        y_factor=factor_pair.y,
        x_factor_familiar_name=familiar_names_translation.get(factor_pair.x.value, factor_pair.x.value),
        y_factor_familiar_name=familiar_names_translation.get(factor_pair.y.value, factor_pair.y.value),
    )

    # write total statistics
    _calculate_overall_default_plot_data_stats(factor_pair, crunched_df, default_plot_data)
    # cut the dataframe into bins and add column with information about into which bucket it belongs
    crunched_df["bucket"] = pd.cut(crunched_df[factor_pair.x.value], bins=x_bucket_intervals)
    # group the data by the buckets
    # pylint: disable=unnecessary-comprehension  -- the short form it sugest does not work
    buckets_of_data = {bucket: group for bucket, group in crunched_df.groupby("bucket", observed=True)}
    # count empty buckets
    _count_and_log_empty_buckets(buckets_of_data, x_bucket_intervals, factor_pair)
    # transform the bucket groups into custom format working bucket
    working_buckets = [
        WorkingBucket(
            interval=bucket_interval,
            factor_pair=factor_pair,
            structure_count=len(bucket_df[factor_pair.x.value]),
            data=bucket_df[[factor_pair.x.value, factor_pair.y.value]]
        ) for bucket_interval, bucket_df in buckets_of_data.items()
    ]
    # find missing intervals between buckets, and extend neighbouring buckets over them if they are in the middle
    _remove_gaps_from_missing_intervals(working_buckets)
    # join small intervals with their neighbours
    working_buckets = _join_small_buckets(working_buckets)
    # create desired data format from the information about buckets and calculate additional information
    default_plot_data.graph_buckets = _create_final_plot_buckets(working_buckets)

    return default_plot_data


def _calculate_overall_default_plot_data_stats(
    factor_pair: FactorPair, crunched_df: pd.DataFrame, default_plot_data: DefaultPlotData
) -> None:
    """
    Calculate and store statistics about the factor pairing on the whole.
    :param factor_pair: Factor pair (on x and y)
    :param crunched_df: Dataframe with crunched csv data
    :param default_plot_data: Instance to store the new stats into.
    """
    default_plot_data.structure_count = len(crunched_df)
    x_factor_series = crunched_df[factor_pair.x.value]
    y_factor_series = crunched_df[factor_pair.y.value]
    default_plot_data.x_factor_global_minimum = x_factor_series.min()
    default_plot_data.x_factor_global_maximum = x_factor_series.max()
    default_plot_data.y_factor_global_minimum = y_factor_series.min()
    default_plot_data.y_factor_global_maximum = y_factor_series.max()


def _count_and_log_empty_buckets(
    used_buckets: dict[pd.Interval, pd.DataFrame], expected_intervals: pd.IntervalIndex, factor_pair: FactorPair
) -> None:
    missing_intervals = []
    for interval in expected_intervals:
        if interval not in used_buckets and not np.isinf(interval.left) and not np.isinf(interval.right):
            # take note of missing intervals, but ignore if the edge ones (with -inf/inf) are empty
            missing_intervals.append(str(interval))

    if missing_intervals:
        logging.info(
            "[%s+%s] %s interval(s) had no structures. Intervals: %s",
            factor_pair.x.value, factor_pair.y.value, len(missing_intervals), missing_intervals
        )


def _remove_gaps_from_missing_intervals(working_buckets: list[WorkingBucket]) -> None:
    """
    If a gap in intervals between buckets is encountered, the bucket with less structures inside of it.
    :param working_buckets: List of working buckets to adjust.
    """
    last_bucket = working_buckets[0]
    for current_bucket in working_buckets[1:]:
        if last_bucket.interval.right < current_bucket.interval.left:
            # if there is a gap in the interval because there were no data in that bucket
            # extend the interval with fewer structures
            if last_bucket.structure_count < current_bucket.structure_count:
                last_bucket.interval = pd.Interval(
                    last_bucket.interval.left, current_bucket.interval.left, closed=last_bucket.interval.closed
                )
            else:
                current_bucket.interval = pd.Interval(
                    last_bucket.interval.right, current_bucket.interval.right, closed=current_bucket.interval.closed
                )
        last_bucket = current_bucket


def _join_small_buckets(working_buckets: list[WorkingBucket], bucket_size_minimum: int = 100) -> list[WorkingBucket]:
    """
    Go through all the working buckets. If any has fewer structures than bucket size minimum, it gets merged with
    the neighbouring one (with the one with fewer structures).
    :param working_buckets: List of working buckets.
    :param bucket_size_minimum: Minimal size of bucket to be left unmerged. Any with fewer structures will get merged.
    :return: List of working buckets after possible merging.
    """
    new_working_buckets = []
    bucket_to_merge = None

    for bucket in working_buckets:
        if bucket_to_merge is not None:
            if new_working_buckets and new_working_buckets[-1].structure_count < bucket.structure_count:
                # merge if previous bucket, if such exists
                new_working_buckets[-1] = _merge_buckets(new_working_buckets[-1], bucket_to_merge)
            else:  # merge with next (current) bucket
                bucket = _merge_buckets(bucket_to_merge, bucket)
            bucket_to_merge = None

        if bucket.structure_count < bucket_size_minimum:
            bucket_to_merge = bucket
        else:
            new_working_buckets.append(bucket)

    if bucket_to_merge is not None:  # if the last bucket itself needs to be merged
        new_working_buckets[-1] = _merge_buckets(new_working_buckets[-1], bucket_to_merge)

    return new_working_buckets


def _merge_buckets(left_bucket: WorkingBucket, right_bucket: WorkingBucket) -> WorkingBucket:
    """
    Merge two buckets. Adjust the resulting interval and join the data.
    :param left_bucket: Bucket on the left side.
    :param right_bucket: Bucket on the right side.
    :return: New merged bucket.
    """
    logging.debug(
        "Merged buckets %s and %s (had %s and %s structures)",
        left_bucket.interval, right_bucket.interval, left_bucket.structure_count, right_bucket.structure_count)
    return WorkingBucket(
        interval=_join_intervals(left_bucket.interval, right_bucket.interval),
        factor_pair=left_bucket.factor_pair,
        structure_count=left_bucket.structure_count + right_bucket.structure_count,
        data=pd.concat([left_bucket.data, right_bucket.data], axis=0)
    )


def _create_final_plot_buckets(working_buckets: list[WorkingBucket]) -> list[DefaultPlotBucket]:
    """
    Process values from working buckets into a final default plot buckets. Inf interval values are removed (replaced by
    min/max values respectivelly) and in case of release date factor, the values of average and quartiles are rounded.
    :param working_buckets: All working buckets.
    :return: All created plot buckets.
    """
    buckets = []
    for i, working_bucket in enumerate(working_buckets):
        buckets.append(_create_final_plot_bucket(working_bucket, i + 1))
    return buckets


def _create_final_plot_bucket(working_bucket: WorkingBucket, ordinal_number: int) -> DefaultPlotBucket:
    """
    Process values from working bucket into a final default plot bucket. Inf interval values are removed (replaced
    by min/max values respectivelly) and in case of date, the values of average and quartiles are rounded.
    :param working_bucket: Bucket with collected information to be processed.
    :param ordinal_number: Ordinal number of the bucket.
    :return: Created default plot bucket.
    """
    final_bucket = DefaultPlotBucket(
        ordinal_number=ordinal_number,
        structure_count=working_bucket.structure_count,
    )

    if np.isinf(working_bucket.interval.left):
        final_bucket.x_factor_from.open_interval = False
        final_bucket.x_factor_from.value = working_bucket.x_factor_data.min()
    else:
        final_bucket.x_factor_from.open_interval = working_bucket.interval.open_left
        final_bucket.x_factor_from.value = working_bucket.interval.left

    if np.isinf(working_bucket.interval.right):
        final_bucket.x_factor_to.open_interval = False
        final_bucket.x_factor_to.value = working_bucket.x_factor_data.max()
    else:
        final_bucket.x_factor_to.open_interval = working_bucket.interval.open_right
        final_bucket.x_factor_to.value = working_bucket.interval.right

    final_bucket.y_factor_average = working_bucket.y_factor_data.mean()
    final_bucket.y_factor_high_quartile = working_bucket.y_factor_data.quantile(0.75)
    final_bucket.y_factor_low_quartile = working_bucket.y_factor_data.quantile(0.25)
    final_bucket.y_factor_median = working_bucket.y_factor_data.median()
    final_bucket.y_factor_maximum = working_bucket.y_factor_data.max()
    final_bucket.y_factor_minimum = working_bucket.y_factor_data.min()

    return final_bucket


def _join_intervals(left: pd.Interval, right: pd.Interval) -> pd.Interval:
    """
    Returns interval with left boundary from the first interval, and right from the second one (including closed/open).
    :param left: Left interval to join.
    :param right: Right interval to join.
    :return: New interval.
    """
    if left.overlaps(right) or left.right != right.left or left.closed_right == right.closed_left:
        raise ValueError(f"Intervals {left} and {right} are incompatible for joining.")

    closedness = "neither"
    if left.closed_left:
        if right.closed_right:
            closedness = "both"
        else:
            closedness = "left"
    elif right.closed_right:
        closedness = "right"

    return pd.Interval(
        left=left.left,
        right=right.right,
        closed=closedness
    )


def _add_inf_boundaries_to_bucket_timits(bucket_limit_series: pd.Series):
    """
    Ignores the first arbitrary value, inserts -inf instead of it. Adds +inf at the end.
    :param bucket_limit_series: Bucket limits series.
    """
    if bucket_limit_series[0] != -0.01:
        logging.warning(
            "First value of x factor bucket limits from csv is assumed to be arbitrary and is replaced by -inf. But the"
            " value found was %s instead of -0.01. Still replacing it by -inf. This may not be the desired behaviour."
        )
    bucket_limit_series[0] = -np.inf
    bucket_limit_series[bucket_limit_series.index[-1] + 1] = np.inf  # add inf to the index +1 than the highest index


def _load_csv_as_dataframe(filepath: str) -> pd.DataFrame:
    """
    Load csv as pandas dataframe (expecting ; delimiter).
    :param filepath: Path to csv file.
    :return: Pandas dataframe.
    """
    try:
        return pd.read_csv(filepath, delimiter=";")
    except (ValueError, OSError) as ex:
        raise ParsingError(f"Failed to load {filepath} csv. {ex}") from ex
