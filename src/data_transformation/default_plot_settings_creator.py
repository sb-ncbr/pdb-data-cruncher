import logging
import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Union, Generator, Optional

import numpy as np
import pandas as pd

from src.models import FactorType
from src.models.transformed import DefaultPlotSettingsItem
from src.exception import DataTransformationError
from src.constants import (
    DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES,
    DEFAULT_PLOT_SETTINGS_MIN_STRUCTURE_COUNT_IN_BUCKET,
    DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT,
    DEFAULT_PLOT_SETTINGS_STD_OUTLIER_MULTIPLIER,
)


class NoXFactorValueError(DataTransformationError):
    """
    Exception raised and caught only in this file, representing no x factors with value in sliced dataframe.
    """


class InvalidBucketSize(ValueError):
    """
    Exception raised and caught only within this file, representing invalid bucket size that cannot be decomposed.
    """


@dataclass(slots=True)
class DecomposedBucketSize:
    """
    Holds information about bucket size in custom "decomposed" way.
    """

    base: int
    multiplier: Decimal

    def to_decimal(self) -> Decimal:
        """
        Return this number in Decimal type.
        """
        return self.base * self.multiplier


@dataclass(slots=True)
class FactorMinMax:
    """
    Holds information about the factor's min/max values while they are being processed.
    """

    factor: FactorType
    min_raw: Union[int, float, None] = None
    max_raw: Union[int, float, None] = None
    effective_min: Optional[Decimal] = None
    effective_max: Optional[Decimal] = None
    bucket_size: Optional[Decimal] = None


def create_default_plot_settings(
    crunched_df: pd.DataFrame, factor_types_translations: dict[FactorType, str]
) -> list[DefaultPlotSettingsItem]:
    default_plot_settings = []

    all_factor_types = list(factor_types_translations.keys())

    for factor_type in factor_types_translations:
        if "PERCENTILE" in factor_type.name:
            continue  # TODO temporary
        if factor_type == FactorType.RELEASE_DATE:
            pass  # TODO needs special handling
        elif not factor_type.binary_type():
            factor_min_max = _calculate_raw_factor_min_max(factor_type, crunched_df, all_factor_types)
            _find_ideal_factor_bucket_size(factor_min_max, crunched_df, all_factor_types)

    # TODO load it into default plot settings

    return default_plot_settings


def _calculate_raw_factor_min_max(
    x_factor_type: FactorType, crunched_df: pd.DataFrame, all_factor_types: list[FactorType]
) -> FactorMinMax:
    """
    For given x factor type, calculate the minimum and maximum raw (= not rounded) value that is common for all the
    possible xy factor combinations.
    :param x_factor_type: Type of factor that will represent the x-axis.
    :param crunched_df: Dataframe loaded with crunched df data.
    :param all_factor_types: List of all factor types.
    :return: Factor min max instance.
    """
    x_factor_min_max = FactorMinMax(x_factor_type)
    x_factor_relevant_df = crunched_df.dropna(subset=[x_factor_type.value])  # dataframe without rows where x was None

    empty_combinations_y_factors = []

    for y_factor_type in all_factor_types:
        try:
            if x_factor_type != y_factor_type:
                xy_factor_relevant_df = x_factor_relevant_df[[x_factor_type.value, y_factor_type.value]].dropna()
                _adjust_raw_factor_min_max(x_factor_min_max, xy_factor_relevant_df)
        except NoXFactorValueError:
            empty_combinations_y_factors.append(y_factor_type)

    if empty_combinations_y_factors:
        raise DataTransformationError(
            f"Factor {x_factor_type.value} could not create default plot settings because it had no values in "
            f"combination with following factors: {empty_combinations_y_factors}"
        )

    return x_factor_min_max


def _adjust_raw_factor_min_max(
    x_factor_min_max: FactorMinMax, xy_factor_relevant_df: pd.DataFrame
) -> None:
    """
    Considers the min and max value for x factor in combination with selected y factor. (Which may be different
    minimal value that with other factor, because some of the data rows may contain Nones for the combination
    and thus are not considered.) The min max are selected after ignoring outliers. If min or max value was
    already set previously by different xy factor combination, it is overwriten only if the new minimal value
    is higher than the previous one, and if the new maximum value is lower than the previous one.
    :param x_factor_min_max: Information about factor type and min/max values found so far.
    :param xy_factor_relevant_df: Dataframe with crunched csv relevant only to this combination of xy factors
    (None values were already dropped for them).
    :raises NoXFactorValue: When the x factor has no values at all.
    """
    x_factor_min, x_factor_max = _get_min_and_max_value_ignoring_outliers(
        xy_factor_relevant_df[x_factor_min_max.factor.value]
    )

    if x_factor_min_max.min_raw is None or x_factor_min > x_factor_min_max.min_raw:
        x_factor_min_max.min_raw = x_factor_min

    if x_factor_min_max.max_raw is None or x_factor_max < x_factor_min_max.max_raw:
        x_factor_min_max.max_raw = x_factor_max


def _get_min_and_max_value_ignoring_outliers(dataset: pd.Series) -> tuple[Union[int, float], Union[int, float]]:
    """
    Get min and max value from given Series, but do not consider outliers.
    :param dataset: Data to get min/max value from.
    :return: Min and max value.
    :raises NoXFactorValue: When the series has no values at all.
    """
    dataset_standard_deviation = dataset.std()
    dataset_mean = dataset.mean()

    if np.isnan(dataset_standard_deviation) or np.isnan(dataset_mean):
        raise NoXFactorValueError()

    lower_bound = dataset_mean - DEFAULT_PLOT_SETTINGS_STD_OUTLIER_MULTIPLIER * dataset_standard_deviation
    upper_bound = dataset_mean + DEFAULT_PLOT_SETTINGS_STD_OUTLIER_MULTIPLIER * dataset_standard_deviation
    filtered_dataset = dataset.where((dataset >= lower_bound) & (dataset <= upper_bound))
    min_value_without_outliers = filtered_dataset.min()
    max_value_without_outliers = filtered_dataset.max()

    # the numpy type would create typing issues later on, coverting for type safety and consistency
    if isinstance(min_value_without_outliers, np.int64):
        min_value_without_outliers = int(min_value_without_outliers)
    elif isinstance(min_value_without_outliers, np.float64):
        min_value_without_outliers = float(min_value_without_outliers)
    if isinstance(max_value_without_outliers, np.int64):
        max_value_without_outliers = int(max_value_without_outliers)
    elif isinstance(max_value_without_outliers, np.float64):
        max_value_without_outliers = float(max_value_without_outliers)

    return min_value_without_outliers, max_value_without_outliers


def _find_ideal_factor_bucket_size(
    factor_min_max: FactorMinMax, crunched_df: pd.DataFrame, all_factor_types: list[FactorType]
):
    """
    For given factor min max (factor type and real min/max values) and dataset, the function finds good bucket size
    and min/max value for these buckets. It finds such bucket size that each bucket it creates has at least
    DEFAULT_PLOT_SETTINGS_MIN_STRUCTURE_COUNT_IN_BUCKET structures no matter which of the possible factors is on
    the y-axis; and so that both the bucket width itself and x values forming the bucket limits are "neat" numbers
    with minimal significant numbers, thus friendly for directly displaying to user. Min/max values on x may
    be significantly cut to allow for meaningful bucket creation (avoiding sparse data around outliers). \n
    The final result is loaded into passed factor min max.
    :param factor_min_max: Information about x factor with factor type and real min/max values.
    :param crunched_df: Dataframe with loaded crunched csv.
    :param all_factor_types: List of all factor types, used to derive all possible factor combinations.
    :raise DataTransformationError: If the buckets cannot be created.
    """
    factor_relevant_df = crunched_df.dropna(
        subset=[factor_min_max.factor.value]
    ).sort_values(by=factor_min_max.factor.value)

    for possible_bucket_size in _possible_neat_bucket_size_generator(factor_min_max):
        bucket_limits = _create_neat_bucket_limits(factor_min_max, possible_bucket_size)
        if _test_possible_bucket_limits(factor_min_max.factor, factor_relevant_df, bucket_limits, all_factor_types):
            # all buckets have enough structures
            factor_min_max.bucket_size = possible_bucket_size
            factor_min_max.effective_min = bucket_limits[0]
            factor_min_max.effective_max = bucket_limits[-1]
            return
        elif len(bucket_limits) == 1:
            # the possible size generator is infinite, but buckets get larger - if the dataset is so small even
            # one bucket would not contain enough structures, this ends the loop
            raise DataTransformationError(
                f"{factor_min_max.factor.value} has less than {DEFAULT_PLOT_SETTINGS_MIN_STRUCTURE_COUNT_IN_BUCKET} "
                "even when all the data fall into one bucket."
            )


def _test_possible_bucket_limits(
    x_factor_type: FactorType, factor_df: pd.DataFrame, bucket_limits: list[Decimal], factor_types: list[FactorType]
) -> bool:
    """
    Check whether given bucket limits create buckets with enough structures for each factor type on y.
    :param x_factor_type: X factor type.
    :param factor_df: Dataframe with cruched data but none values for x factor were dropped.
    :param bucket_limits: List of values forming limits of buckets to test.
    :param factor_types: All factor types possible on y-axis.
    :return: False if the buckets are not satisfactory, True if they are.
    """
    # bucket limits are decimals to keep precision for the final output; but for cutting the data to approximately
    # check there is enough data in each bucket, it is ok to use them as float (decimals cannot be used for cut)
    float_bucket_limits = [float(limit) for limit in bucket_limits]
    factor_df["bucket"] = pd.cut(
        factor_df[x_factor_type.value], bins=float_bucket_limits, right=False
    )
    buckets_df = {bucket: group for bucket, group in factor_df.groupby("bucket", observed=True)}

    # check if there is at least N strucutres (df lines) at all (this counts even none values for now)
    for bucket_df in buckets_df.values():
        if len(bucket_df) < DEFAULT_PLOT_SETTINGS_MIN_STRUCTURE_COUNT_IN_BUCKET:
            return False

        for y_factor in factor_types:
            if y_factor == x_factor_type:  # y is the same as x factor
                continue
            if bucket_df[y_factor.value].count() < DEFAULT_PLOT_SETTINGS_MIN_STRUCTURE_COUNT_IN_BUCKET:
                return False

    # if it got here, the buckets sizes are ok
    return True


def _create_neat_bucket_limits(factor_min_max: FactorMinMax, bucket_size: Decimal) -> list[Decimal]:
    """
    For given collected factor min max info and given bucket size, the function creates such values that mark
    the edges of the buckets covering the factor data. The bucket limits will be "neat" - made in such way
    that they are divisible by the bucket size itself. (And given the bucket size is human friendly number, with
    only 1-2 significant numbers, the new limits will also be relatively nice to read.)
    :param factor_min_max: Relevant information about x factor values.
    :param bucket_size: Predetermined bucket size.
    :return: List representing the bucket limit values.
    """
    limits = []
    current_limit = (Decimal(factor_min_max.min_raw) // bucket_size) * bucket_size
    limits.append(current_limit)

    while current_limit < factor_min_max.max_raw:
        current_limit += bucket_size
        limits.append(current_limit)

    return limits


def _possible_neat_bucket_size_generator(factor_min_max: FactorMinMax) -> Generator[Decimal, None, None]:
    """
    Returns generator creating neat (rounded to specific values) bucket sizes. First bucket size returned will be
    the smallest possible (creating the max number of buckets based on DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT).
    Subsequent bucket sizes are bigger and bigger, while always beeing one of the allowed neat sizes multiplied
    by 10^n.
    :param factor_min_max: Holds information about factor's min/max values for plot settings.
    :return: Generator generating the numbers.
    :raises DataTransformationError: When the bucket size cannot be created.
    """
    min_bucket_size_raw = (factor_min_max.max_raw - factor_min_max.min_raw) / DEFAULT_PLOT_SETTINGS_MAX_BUCKET_COUNT
    try:
        bucket_size = _decompose_and_round_bucket_size(Decimal(min_bucket_size_raw))
    except InvalidBucketSize:
        raise DataTransformationError(
            f"Neat bucket creation failed for {factor_min_max.factor.value}. Min bucket size was negative or zero, "
            f"most likely result of too aggresive funciton that removes outlier values. Adjusted min value: "
            f"'{factor_min_max.min_raw}', adjusted max value: '{factor_min_max.max_raw}'."
        )

    allowed_size_index = _match_minimal_size_to_allowed_sizes(
        bucket_size, DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES
    )

    yield bucket_size.to_decimal()
    while True:
        allowed_size_index += 1
        if allowed_size_index == len(DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES):
            allowed_size_index = 0
            bucket_size.multiplier *= 10
        bucket_size.base = DEFAULT_PLOT_SETTINGS_ALLOWED_BUCKET_BASE_SIZES[allowed_size_index]
        yield bucket_size.to_decimal()


def _match_minimal_size_to_allowed_sizes(bucket_size: DecomposedBucketSize, allowed_sizes: list[int]) -> int:
    """
    Finds the smallest value from allowed sizes that is bigger than the base number in bucket size, sets the
    base value of bucket_size to it and returns the index of that value from allowed sizes. If the base value is
    bigger than all the allowed sizes, it sets it to the first allowed size and multiplices the bucket size
    multipler by 10. \n
    Example: \n
    bucket_size (base: 12, mult. 100), allowed_sizes [10, 25, 50, 75]
    => sets base to 25, returns index 1 \n
    bucket_size (base: 92, mult. 100), allowed_sizes [10, 25, 50, 75]
    => sets base to 10, multiplier to 1000, returns index 0
    :param bucket_size: Bucket size with base <10,99> and multipler that is 10**n that will be matched to allowed size.
    :param allowed_sizes: List of allowed sizes bucket_size.base is allowed to be after this operation.
    :return: Index of the matched size in allowed_sizes.
    """
    width_index = -1
    for i, width in enumerate(allowed_sizes):
        if bucket_size.base < width:
            width_index = i
            bucket_size.base = width
            break

    if width_index == -1:
        width_index = 0
        bucket_size.base = allowed_sizes[0]
        bucket_size.multiplier *= 10  # for numbers with bucket size base over the last width base, it overflows

    return width_index


def _decompose_and_round_bucket_size(number: Decimal) -> DecomposedBucketSize:
    """
    Take given number and decompose it into DecomposedBucketSize. Rounds the decomposed part to two significant digits.
    :param number: Number to decompose.
    :return: Decomposed number.
    :raises InvalidBucketSize: If the number to decompose is zero or negative.
    """
    if number <= 0:
        raise InvalidBucketSize()

    (_, digits, digit_exponent) = number.as_tuple()
    number_exponent = len(digits) + digit_exponent - 1
    # create number mantissa rounded to two significant numbers
    if len(digits) > 2:
        number_base = math.ceil(digits[0] * 10 + digits[1] + digits[2] * Decimal("0.1"))
    elif len(digits) > 1:
        number_base = digits[0] * 10 + digits[1]
    else:
        number_base = digits[0]

    # Decimal conversions to ensure result is Decimal not suffering from float imprecision
    number_multiplicator = Decimal(10) ** Decimal(number_exponent - 1)
    return DecomposedBucketSize(number_base, number_multiplicator)
