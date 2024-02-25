from dataclasses import dataclass
from typing import Optional, Union


@dataclass(slots=True)
class DefaultPlotSettingsItem:
    bucked_width: Optional[float] = None
    x_factor_familiar_name: Optional[str] = None
    x_limit_lower: Union[float, int, None] = None
    x_limit_upper: Union[float, int, None] = None
    y_factor_familiar_name: Optional[str] = None
    y_limit_lower: Union[float, int, None] = None
    y_limit_upper: Union[float, int, None] = None
    no_minimum: Optional[bool] = None
    no_maximum: Optional[bool] = None

    def to_dict(self):
        return {
            "BucketWidth": self.bucked_width,
            "Factor": self.x_factor_familiar_name,
            "XlimitLower": self.x_limit_lower,
            "XlimitUpper": self.x_limit_upper,
        }
