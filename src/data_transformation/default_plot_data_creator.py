import logging
from dataclasses import dataclass, field

import pandas as pd

from src.models.transformed import DefaultPlotBucket, DefaultPlotData, FactorPair
from src.exception import ParsingError, DataTransformationError
from src.constants import BUCKET_SIZE_MINIMUM


@dataclass
class WorkingBucket:
    interval: pd.Interval
    factor_pair: FactorPair
    structure_count: int = 0
    data: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def x_factor_data(self):
        return self.data[self.factor_pair.x_factor.value]

    @property
    def y_factor_data(self):
        return self.data[self.factor_pair.y_factor.value]


def create_default_plot_data(
        crunched_csv_filepath: str,
        x_factor_bucket_limits_filepath: str,
        factor_pairs: list[FactorPair],
        familiar_names_translation: dict[str, str]
) -> list[DefaultPlotData]:
    default_plot_data = []
    crunched_df = _load_csv_as_dataframe(crunched_csv_filepath)
    bucket_limits_df = _load_csv_as_dataframe(x_factor_bucket_limits_filepath)
    failed_factor_pairs_count = 0

    for factor_pair in factor_pairs:
        logging.debug("Processing default plot data for pair '%s+%s'", factor_pair.x_factor.value, factor_pair.y_factor.value)
        try:
            factor_pair_crunched_df = crunched_df[[factor_pair.x_factor.value, factor_pair.y_factor.value]]
            factor_pair_crunched_df = factor_pair_crunched_df.dropna()  # drops rows with at least one None
            x_bucket_limit_series = bucket_limits_df[factor_pair.x_factor.value].dropna()
            single_plot_data = _create_default_plot_data_for_factor_pair(
                factor_pair,
                factor_pair_crunched_df,
                x_bucket_limit_series,
                familiar_names_translation
            )
            default_plot_data.append(single_plot_data)
        except (KeyError, ValueError) as ex:
            logging.warning(
                "Factor pair (%s, %s) cannot be processed because of %s: %s",
                factor_pair.x_factor.value,
                factor_pair.y_factor.value,
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
    x_bucket_limit_series: pd.Series,
    familiar_names_translation: dict[str, str]
) -> DefaultPlotData:
    default_plot_data = DefaultPlotData(
        x_factor=factor_pair.x_factor,
        y_factor=factor_pair.y_factor,
        x_factor_familiar_name=familiar_names_translation.get(factor_pair.x_factor.value, factor_pair.x_factor.value),
        y_factor_familiar_name=familiar_names_translation.get(factor_pair.y_factor.value, factor_pair.y_factor.value),
    )

    # cut the dataframe into bins and add column with information about into which bucket it belongs
    crunched_df["bucket"] = pd.cut(crunched_df[factor_pair.x_factor.value], bins=x_bucket_limit_series, right=False)
    # group the data by the buckets
    buckets = {bucket: group for bucket, group in crunched_df.groupby("bucket", observed=True)}
    # transform the bucket groups into custom format working bucket
    working_buckets = [
        WorkingBucket(
            interval=bucket_interval,
            factor_pair=factor_pair,
            structure_count=len(bucket_df[factor_pair.x_factor.value]),
            data=bucket_df[[factor_pair.x_factor.value, factor_pair.y_factor.value]]
        ) for bucket_interval, bucket_df in buckets.items()
    ]
    # join small intervals with their neighbours
    working_buckets = _join_small_buckets(working_buckets)
    # create desired data format from the information about buckets and calculate additional information
    default_plot_data.graph_buckets = _create_final_plot_buckets(working_buckets)

    return default_plot_data


def _join_small_buckets(working_buckets: list[WorkingBucket]) -> list[WorkingBucket]:
    new_working_buckets = []
    bucket_to_merge = None
    for bucket in working_buckets:
        if bucket_to_merge is not None:
            bucket.interval = _join_intervals(left=bucket_to_merge.interval, right=bucket.interval)
            bucket.structure_count += bucket_to_merge.structure_count
            bucket.data = pd.concat([bucket_to_merge.data, bucket.data], axis=0)
            bucket_to_merge = None

        if bucket.structure_count < 1:
            bucket_to_merge = bucket
        else:
            new_working_buckets.append(bucket)

    # if last interval needs to be merged
    if bucket_to_merge is not None:
        new_working_buckets[-1].interval = _join_intervals(
            left=new_working_buckets[-1].interval,
            right=bucket_to_merge.interval,
        )
        new_working_buckets[-1].structure_count += bucket_to_merge.structure_count
        new_working_buckets[-1].data = pd.concat([new_working_buckets[-1].data, bucket_to_merge.data], axis=0)

    return new_working_buckets


def _create_final_plot_buckets(working_buckets: list[WorkingBucket]) -> list[DefaultPlotBucket]:
    buckets = []
    for i, working_bucket in enumerate(working_buckets):
        buckets.append(_create_final_plot_bucket(working_bucket, i + 1))
    return buckets


def _create_final_plot_bucket(working_bucket: WorkingBucket, ordinal_number: int) -> DefaultPlotBucket:
    final_bucket = DefaultPlotBucket(
        ordinal_number=ordinal_number,
        structure_count=working_bucket.structure_count,
    )
    final_bucket.x_factor_from.open_interval = working_bucket.interval.open_left
    final_bucket.x_factor_from.value = working_bucket.interval.left
    final_bucket.x_factor_to.open_interval = working_bucket.interval.open_right
    final_bucket.x_factor_to.value = working_bucket.interval.right

    # TODO what to do with .0 values for strict ints (like year)
    final_bucket.y_factor_average = working_bucket.y_factor_data.mean()
    final_bucket.y_factor_high_quartile = working_bucket.y_factor_data.quantile(0.75)
    final_bucket.y_factor_low_quartile = working_bucket.y_factor_data.quantile(0.25)
    final_bucket.y_factor_maximum = working_bucket.y_factor_data.max()
    final_bucket.y_factor_minimum = working_bucket.y_factor_data.min()
    final_bucket.y_factor_median = working_bucket.y_factor_data.median()

    return final_bucket


def _join_intervals(left: pd.Interval, right: pd.Interval) -> pd.Interval:
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


def _load_csv_as_dataframe(filepath: str) -> pd.DataFrame:
    try:
        return pd.read_csv(filepath, delimiter=";")
    except (ValueError, OSError) as ex:
        raise ParsingError(f"Failed to load {filepath} csv. {ex}") from ex
