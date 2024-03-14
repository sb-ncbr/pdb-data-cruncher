import logging
from dataclasses import dataclass
from typing import Union

import numpy as np
import pandas as pd

from src.models import FactorType
from src.models.transformed import DefaultPlotSettingsItem
from src.exception import DataTransformationError


class NoXFactorValueError(DataTransformationError):
    """
    Exception raised and caught only in this file, representing no x factors with value in sliced dataframe.
    """


@dataclass(slots=True)
class FactorMinMax:
    factor: FactorType
    min_value: Union[int, float, None] = None
    max_value: Union[int, float, None] = None


def create_default_plot_settings(
    crunched_df: pd.DataFrame, factor_types_translations: dict[FactorType, str]
) -> list[DefaultPlotSettingsItem]:
    default_plot_settings = []

    all_factor_types = list(factor_types_translations.keys())
    factor_min_max_list = []
    for factor_type in factor_types_translations:
        factor_min_max_list.append(_calculate_factor_combo_min_max(factor_type, crunched_df, all_factor_types))


    # TODO create buckets

    # TODO load it into default plot settings

    return default_plot_settings


def _calculate_factor_combo_min_max(
    x_factor_type: FactorType, crunched_df: pd.DataFrame, all_factor_types: list[FactorType]
) -> FactorMinMax:
    x_factor_min_max = FactorMinMax(x_factor_type)
    x_factor_relevant_df = crunched_df.dropna(subset=[x_factor_type.value])  # dataframe without rows where x was None
    empty_combinations_y_factors = []

    for y_factor_type in all_factor_types:
        try:
            if x_factor_type != y_factor_type:
                xy_factor_relevant_df = x_factor_relevant_df[[x_factor_type.value, y_factor_type.value]].dropna()
                _adjust_factor_combo_min_max(x_factor_type, x_factor_min_max, xy_factor_relevant_df)
        except NoXFactorValueError:
            empty_combinations_y_factors.append(y_factor_type)

    if empty_combinations_y_factors:
        raise DataTransformationError(
            f"Factor {x_factor_type.value} could not create default plot settings because it had no values in "
            f"combination with following factors: {empty_combinations_y_factors}"
        )

    return x_factor_min_max


def _adjust_factor_combo_min_max(
    x_factor_type: FactorType,
    x_factor_min_max: FactorMinMax,
    xy_factor_relevant_df: pd.DataFrame
) -> None:
    x_factor_min = xy_factor_relevant_df[x_factor_type.value].min()
    x_factor_max = xy_factor_relevant_df[x_factor_type.value].max()

    if np.isnan(x_factor_min) or np.isnan(x_factor_max):
        raise NoXFactorValueError()

    if x_factor_min_max.min_value is None or x_factor_min > x_factor_min_max.min_value:
        x_factor_min_max.min_value = x_factor_min

    if x_factor_min_max.max_value is None or x_factor_max < x_factor_min_max.max_value:
        x_factor_min_max.max_value = x_factor_max
