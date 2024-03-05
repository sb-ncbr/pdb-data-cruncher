from dataclasses import dataclass, field
from typing import Optional, Union

from src.models import FactorType


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

    def to_dict(self):
        """
        Create a dictionary out of self for default plot data json.
        :return: The dict.
        """
        return {
            "BucketOrdinalNumber": str(self.ordinal_number),
            "StructureCountInBucket": str(self.structure_count),
            "XfactorFrom": {
                "XfactorFromIsInfinity": False,  # no longer used, but needs to be present for backwards compatibility
                "XfactorFromOpenInterval": self.x_factor_from.open_interval,
                "XfactorFromValue": str(self.x_factor_from.value),
            },
            "XfactorTo": {
                "XfactorToIsInfinity": False,  # no longer used, but needs to be present for backwards compatibility
                "XfactorToOpenInterval": self.x_factor_to.open_interval,
                "XfactorToValue": str(self.x_factor_to.value),
            },
            "YfactorAverage": str(self.y_factor_average),
            "YfactorHighQuartile": str(self.y_factor_high_quartile),
            "YfactorLowQuartile": str(self.y_factor_low_quartile),
            "YfactorMaximum": str(self.y_factor_maximum),
            "YfactorMedian": str(self.y_factor_median),
            "YfactorMinimum": str(self.y_factor_minimum),
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
        return {
            "GraphBuckets": [bucket.to_dict() for bucket in self.graph_buckets],
            "StructureCount": str(self.structure_count),
            "XfactorGlobalMaximum": str(self.x_factor_global_maximum),
            "XfactorGlobalMinimum": str(self.x_factor_global_minimum),
            "XfactorName": self.x_factor_familiar_name,
            "YfactorGlobalMaximum": str(self.y_factor_global_maximum),
            "YfactorGlobalMinimum": str(self.y_factor_global_minimum),
            "YfactorName": self.y_factor_familiar_name,
        }
