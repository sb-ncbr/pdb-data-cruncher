from dataclasses import dataclass, field
from typing import Optional, Union

from src.models import FactorType
from src.utils import round_decimal_place_relative


@dataclass(slots=True)
class XFactorBoundary:
    """
    Values represent one boundary of x factor interval.
    """

    open_interval: bool = False
    value: Union[float, int, None] = None


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class DefaultPlotBucket:
    """
    Holds information about one plot bucket.
    """

    ordinal_number: int
    structure_count: Optional[int] = None
    x_factor_from: XFactorBoundary = field(default_factory=XFactorBoundary)
    x_factor_to: XFactorBoundary = field(default_factory=XFactorBoundary)
    y_factor_average: Union[float, int, None] = None
    y_factor_high_quartile: Union[float, int, None] = None
    y_factor_low_quartile: Union[float, int, None] = None
    y_factor_maximum: Union[float, int, None] = None
    y_factor_median: Union[float, int, None] = None
    y_factor_minimum: Union[float, int, None] = None

    def to_dict(self, x_is_release_date: bool = False, y_is_release_date: bool = False):
        """
        Create a dictionary out of self for default plot data json.
        :return: The dict.
        """
        x_rounding = round_decimal_place_relative
        y_rounding = round_decimal_place_relative
        if x_is_release_date:  # release date always needs round to whole number
            x_rounding = round
        if y_is_release_date:
            y_rounding = round

        return {
            "BucketOrdinalNumber": str(self.ordinal_number),
            "StructureCountInBucket": str(self.structure_count),
            "XfactorFrom": {
                "XfactorFromIsInfinity": False,  # no longer used, but needs to be present for backwards compatibility
                "XfactorFromOpenInterval": self.x_factor_from.open_interval,
                "XfactorFromValue": str(x_rounding(self.x_factor_from.value)),
            },
            "XfactorTo": {
                "XfactorToIsInfinity": False,  # no longer used, but needs to be present for backwards compatibility
                "XfactorToOpenInterval": self.x_factor_to.open_interval,
                "XfactorToValue": str(x_rounding(self.x_factor_to.value)),
            },
            "YfactorAverage": str(y_rounding(self.y_factor_average)),
            "YfactorHighQuartile": str(y_rounding(self.y_factor_high_quartile)),
            "YfactorLowQuartile": str(y_rounding(self.y_factor_low_quartile)),
            "YfactorMaximum": str(y_rounding(self.y_factor_maximum)),
            "YfactorMedian": str(y_rounding(self.y_factor_median)),
            "YfactorMinimum": str(y_rounding(self.y_factor_minimum)),
        }


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class DefaultPlotData:
    """
    Holds data about the whole default plot data for one factor pair combination.
    """

    x_factor: FactorType
    y_factor: FactorType
    graph_buckets: list[DefaultPlotBucket] = field(default_factory=list)
    structure_count: Optional[int] = None
    x_factor_global_maximum: Union[float, int, None] = None
    x_factor_global_minimum: Union[float, int, None] = None
    x_factor_familiar_name: Optional[str] = None
    y_factor_global_maximum: Union[float, int, None] = None
    y_factor_global_minimum: Union[float, int, None] = None
    y_factor_familiar_name: Optional[str] = None

    def to_dict(self):
        """
        Create a dictionary out of self for default plot data json.
        :return: The dict.
        """
        x_is_release_date = self.x_factor == FactorType.RELEASE_DATE
        y_is_release_date = self.y_factor == FactorType.RELEASE_DATE
        return {
            "GraphBuckets": [bucket.to_dict(x_is_release_date, y_is_release_date) for bucket in self.graph_buckets],
            "StructureCount": str(self.structure_count),
            "XfactorGlobalMaximum": str(round_decimal_place_relative(self.x_factor_global_maximum)),
            "XfactorGlobalMinimum": str(round_decimal_place_relative(self.x_factor_global_minimum)),
            "XfactorName": self.x_factor_familiar_name,
            "YfactorGlobalMaximum": str(round_decimal_place_relative(self.y_factor_global_maximum)),
            "YfactorGlobalMinimum": str(round_decimal_place_relative(self.y_factor_global_minimum)),
            "YfactorName": self.y_factor_familiar_name,
        }
