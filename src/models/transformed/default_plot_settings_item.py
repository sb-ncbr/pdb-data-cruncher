from dataclasses import dataclass
from decimal import Decimal
from typing import Union


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class DefaultPlotSettingsItem:
    """
    Holds extracted information about default plot settings.
    """

    bucked_width: Union[Decimal, int]
    x_factor_familiar_name: str
    x_limit_lower: Union[Decimal, int]
    x_limit_upper: Union[Decimal, int]

    def to_dict(self):
        """
        Create a dictionary out of self for default plot settings json.
        :return: The dict.
        """
        return {
            # convert to float because Decimal is not json serializable, but precision will not be lost as
            # no more operations are made with it
            "BucketWidth": float(self.bucked_width),
            "Factor": self.x_factor_familiar_name,
            "XlimitLower": float(self.x_limit_lower),
            "XlimitUpper": float(self.x_limit_upper),
        }
