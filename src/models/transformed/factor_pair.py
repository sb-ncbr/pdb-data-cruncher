from dataclasses import dataclass


@dataclass(slots=True)
class FactorPair:
    x_factor: str
    y_factor: str
