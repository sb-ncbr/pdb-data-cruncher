from dataclasses import dataclass

from src.models.factor_type import FactorType


@dataclass(slots=True)
class FactorPair:
    x_factor: FactorType
    y_factor: FactorType
