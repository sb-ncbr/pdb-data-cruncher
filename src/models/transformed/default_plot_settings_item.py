from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Union


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class DefaultPlotSettingsItem:
    """
    Holds extracted information about default plot settings.
    """

    bucked_width: Decimal
    x_factor_familiar_name: str
    x_limit_lower: Decimal
    x_limit_upper: Decimal

    def to_dict(self):
        """
        Create a dictionary out of self for default plot settings json.
        :return: The dict.
        """
        return {
            "BucketWidth": float(self.bucked_width),
            "Factor": self.x_factor_familiar_name,
            "XlimitLower": float(self.x_limit_lower),
            "XlimitUpper": float(self.x_limit_upper),
        }
