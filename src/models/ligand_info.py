from dataclasses import dataclass


@dataclass(slots=True)
class LigandInfo:
    """
    Dataclass holding information about a ligand.
    """

    heavy_atom_count: int
    flexibility: float
