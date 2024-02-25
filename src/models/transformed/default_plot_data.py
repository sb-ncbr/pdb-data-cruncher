from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass(slots=True)
class XFactorBoundary:
    is_infinity: bool = False
    open_interval: bool = False
    value: Union[float, int, None] = None


@dataclass(slots=True)
class DefaultPlotBucket:
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
        return {
            "BucketOrdinalNumber": str(self.ordinal_number),
            "StructureCountInBucket": str(self.structure_count),
            "XfactorFrom": {
                "XfactorFromIsInfinity": self.x_factor_from.is_infinity,
                "XfactorFromOpenInterval": self.x_factor_from.open_interval,
                "XfactorFromValue": str(self.x_factor_from.value),
            },
            "XfactorTo": {
                "XfactorToIsInfinity": self.x_factor_to.is_infinity,
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


@dataclass(slots=True)
class DefaultPlotData:
    x_factor_name: str
    y_factor_name: str
    graph_buckets: list[DefaultPlotBucket] = field(default_factory=list)

    def to_dict(self):
        return {
            "GraphBuckets": [bucket.to_dict() for bucket in self.graph_buckets]
        }
