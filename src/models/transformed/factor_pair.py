from dataclasses import dataclass

from src.models.factor_type import FactorType


@dataclass(slots=True)
class FactorPair:
    """
    Factor pair holding factors for x and y axes.
    """
    x: FactorType
    y: FactorType
