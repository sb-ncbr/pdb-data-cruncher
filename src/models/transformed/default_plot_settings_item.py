from dataclasses import dataclass
from typing import Optional, Union


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class DefaultPlotSettingsItem:
    """
    Holds extracted information about default plot settings.
    """

    bucked_width: Optional[float] = None
    x_factor_familiar_name: Optional[str] = None
    x_limit_lower: Union[float, int, None] = None
    x_limit_upper: Union[float, int, None] = None

    def to_dict(self):
        """
        Create a dictionary out of self for default plot data json.
        :return: The dict.
        """
        return {
            "BucketWidth": self.bucked_width,
            "Factor": self.x_factor_familiar_name,
            "XlimitLower": self.x_limit_lower,
            "XlimitUpper": self.x_limit_upper,
        }
