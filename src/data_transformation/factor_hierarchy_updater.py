import decimal
import logging
import math
from decimal import Decimal
from dataclasses import dataclass

import pandas as pd

from src.exception import DataTransformationError
from src.models import FactorType
from src.config import FactorHierarchySettings
from src.utils import ceiling_relative, floor_relative


@dataclass(slots=True)
class ValuesToUpdate:
    """
    Class created and consumed only in this file, holding processed information to be saved.
    """

    value_range_from: Decimal
    value_range_to: Decimal
    slider_step: Decimal


def update_factor_hierarchy(
    factor_hierarchy_json: dict,
    crunched_df: pd.DataFrame,
    factor_types_translations: dict[FactorType, str],
    fh_config: FactorHierarchySettings
):
    """
    Update given factor hierarchy json with freshly calculated ValueRangeFrom, ValueRangeTo and SliderStep values.
    The calculation is done by data present in crunched dataframe.
    :param factor_hierarchy_json: Json holding the full content of factor hierarchy json. This will be updated
    with new values.
    :param crunched_df: Dataframe loaded with crunched csv.
    :param factor_types_translations: Dictionary translating FactorType into familiar name string.
    :param fh_config: Part of configuration with settings tweaking the numerical thresholds for creating the
    updated values.
    """
    factor_types_translations_reverse = {value: key for key, value in factor_types_translations.items()}
    factor_hierarchy_list = factor_hierarchy_json.get("FactorList")
    failed_factors_count = 0

    if not factor_hierarchy_list:
        raise DataTransformationError("No 'FactorList' item found in factor hierarchy json.")

    for factor_json in factor_hierarchy_list:
        factor_familiar_name = factor_json.get("FactorName", "[no FactorName found in FactorList item]")
        factor_type = factor_types_translations_reverse.get(factor_familiar_name)
        if factor_type is None:
            logging.warning("Failed to translate name '%s' into factor type.", factor_familiar_name)
            failed_factors_count += 1
            continue

        try:
            values_to_update = _create_values_to_update(crunched_df[factor_type.value], fh_config, factor_type)
            _update_values_in_factor_json(factor_json, values_to_update)
        except DataTransformationError as ex:
            logging.warning(
                "Factor '%s' (factor type '%s') failed to update: %s", factor_familiar_name, factor_type.value, ex
            )
            failed_factors_count += 1
        except KeyError:
            logging.warning("Factor '%s' was not found in columns of crunched data.", factor_type.value)
            failed_factors_count += 1

    if failed_factors_count > 0:
        raise DataTransformationError(f"{failed_factors_count} items in FactorList failed to be updated.")


def _create_values_to_update(
    factor_series: pd.Series, fh_config: FactorHierarchySettings, factor_type: FactorType
) -> ValuesToUpdate:
    """
    Create values that are to be updated. Rounds to two significant digits in case of anything that does not
    represent year value.
    :param factor_series: Series from crunched csv related to this factor.
    :param fh_config: Part of configuration with settings tweaking the numerical thresholds for creating the
    updated values.
    :param factor_type: FactorType of currently processed factor.
    :return: Extracted values to be updated in factor hierarchy json.
    """
    if factor_type.is_year():
        return _create_values_to_update_for_year(factor_series, fh_config)
    return _create_values_to_update_for_normal_numbers(factor_series, fh_config, factor_type)


def _create_values_to_update_for_year(
    factor_series: pd.Series, fh_config: FactorHierarchySettings
) -> ValuesToUpdate:
    """
    Create values that are to be updated for values representing year.
    :param factor_series: Series from crunched csv related to this factor.
    :param fh_config: Part of configuration with settings tweaking the numerical thresholds for creating the
    updated values.
    :return: Extracted values to be updated in factor hierarchy json.
    """
    if 10 not in fh_config.allowed_slider_size_bases:
        logging.warning(
            "10 was not allowed as a base for factor hierarchy slider step, but '1' will still be used for year values."
        )

    return ValuesToUpdate(
        value_range_from=Decimal(int(factor_series.min())),
        value_range_to=Decimal(int(factor_series.max())),
        slider_step=Decimal("1"),
    )


def _create_values_to_update_for_normal_numbers(
    factor_series: pd.Series, fh_config: FactorHierarchySettings, factor_type: FactorType
) -> ValuesToUpdate:
    """
    Create values that are to be updated for values represetnting normal numbers. They will be rounded/floored/ceiled
    to precision 2.
    :param factor_series: Series from crunched csv related to this factor.
    :param fh_config: Part of configuration with settings tweaking the numerical thresholds for creating the
    updated values.
    :param factor_type: FactorType of currently processed factor.
    :return: Extracted values to be updated in factor hierarchy json.
    """
    max_raw = ceiling_relative(Decimal(str(factor_series.max())), precision=2)
    # get min value by rounding real min value to the floor to the precision as max_factor_value_raw has
    min_adjusted = Decimal(str(factor_series.min())).quantize(max_raw, rounding=decimal.ROUND_FLOOR)

    minimal_range = max_raw - min_adjusted
    if minimal_range == 0:
        raise DataTransformationError(
            f"The adjusted minimal value ({min_adjusted}) and maximal value ({max_raw}) were the same "
            f"value. Check the source data."
        )

    slider_step_adjusted, interval_count = _find_optimal_slider_step(minimal_range, fh_config)
    max_adjusted = min_adjusted + interval_count * slider_step_adjusted

    if max_adjusted < max_raw:
        logging.warning(
            "Double check code: raw max value was bigger value than adjusted max value. (%s < %s) %s",
            max_adjusted,
            max_raw,
            factor_type.value,
        )

    return ValuesToUpdate(
        value_range_from=min_adjusted,
        value_range_to=max_adjusted,
        slider_step=slider_step_adjusted,
    )


def _find_optimal_slider_step(value_range_to_cover: Decimal, fh_config: FactorHierarchySettings) -> tuple[Decimal, int]:
    slider_step_for_max_intervals = _ceiling_slider_step_to_allowed_values(
        ceiling_relative(Decimal(value_range_to_cover / fh_config.max_interval_count), precision=2),
        fh_config.allowed_slider_size_bases)
    max_intervals_count = math.ceil(value_range_to_cover / slider_step_for_max_intervals)
    max_intervals_diff_to_goal = abs(max_intervals_count - fh_config.ideal_interval_count)

    slider_step_for_min_intervals = _ceiling_slider_step_to_allowed_values(
        floor_relative(Decimal(value_range_to_cover / fh_config.min_interval_count), precision=2),
        fh_config.allowed_slider_size_bases)
    min_intervals_count = math.ceil(value_range_to_cover / slider_step_for_min_intervals)
    min_intervals_diff_to_goal = abs(min_intervals_count - fh_config.ideal_interval_count)

    ideal_slider_step = _ceiling_slider_step_to_allowed_values(
        floor_relative(Decimal(value_range_to_cover / fh_config.ideal_interval_count), precision=2),
        fh_config.allowed_slider_size_bases
    )
    ideal_intervals_count = math.ceil(value_range_to_cover / ideal_slider_step)
    ideal_intervals_diff_to_goal = abs(ideal_intervals_count - fh_config.ideal_interval_count)

    if ideal_intervals_count > max_intervals_count or max_intervals_diff_to_goal < ideal_intervals_diff_to_goal:
        # in case of edge case rounding that would push it out of the bounds, or if max intervals actually resulted
        # in better intervals - both can theoretically happen because of different rounding strategies used
        return slider_step_for_max_intervals, max_intervals_count
    if ideal_intervals_count < min_intervals_count or min_intervals_diff_to_goal < ideal_intervals_diff_to_goal:
        return slider_step_for_min_intervals, min_intervals_count

    return ideal_slider_step, ideal_intervals_count


def _ceiling_slider_step_to_allowed_values(slider_step_raw: Decimal, allowed_slider_size_bases: list[int]) -> Decimal:
    """
    Round up given slider step, so it is one of the allowed sizes * 10^N. E.g. 13 with allowed sizes [10,20,25,50] -> 20
    :param slider_step_raw: Slider step to round up. Assumed to be already rounded to two significant digits.
    :param allowed_slider_size_bases: List of integer values from interval <10,99> that final slider step can have
    as a base value without the exponent.
    :return: Ceiled number.
    """
    # assumes it is already rounded to 2 precision
    (_, digits, digit_exponent) = slider_step_raw.as_tuple()
    number_exponent = len(digits) + digit_exponent - 1

    two_digits_as_number = 10 * digits[0]
    if len(digits) > 1:
        two_digits_as_number += digits[1]

    if two_digits_as_number in allowed_slider_size_bases:
        return slider_step_raw  # no change needed

    for allowed_value in allowed_slider_size_bases:
        if two_digits_as_number < allowed_value:
            return allowed_value * Decimal("10") ** Decimal(number_exponent - 1)

    # if it got here, it is larger than the last size base
    return allowed_slider_size_bases[0] * Decimal("10") ** Decimal(number_exponent)


def _update_values_in_factor_json(factor_json: dict, values_to_update: ValuesToUpdate) -> None:
    """
    Put given values to update into their predefined properties in factor json.
    :param factor_json: Part of hierarchy json representing one factor's item in FactorList.
    :param values_to_update: Values to insert.
    """
    factor_json["ValueRangeFrom"] = str(values_to_update.value_range_from)
    factor_json["ValueRangeTo"] = str(values_to_update.value_range_to)
    factor_json["SliderStep"] = str(values_to_update.slider_step)
