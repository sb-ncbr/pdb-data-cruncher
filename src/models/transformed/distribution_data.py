from dataclasses import dataclass, field
from typing import Union, Optional, Any

from src.models import FactorType
from src.utils import round_relative


@dataclass(slots=True)
class DistributionDataBucket:
    x_from: Union[float, int, None] = None
    x_to: Union[float, int, None] = None
    is_interval: bool = False
    structure_count: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "Xfrom": str(round_relative(self.x_from)),
            "XisInterval": self.is_interval,
            "Xto": str(round_relative(self.x_to)),
            "YstructureCount": str(self.structure_count),
        }


@dataclass(slots=True)
class DistributionData:
    factor_type: FactorType
    factor_familiar_name: str
    buckets: list[DistributionDataBucket] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "Bins": [bucket.to_dict() for bucket in self.buckets],
            "Factor": self.factor_familiar_name,
        }
