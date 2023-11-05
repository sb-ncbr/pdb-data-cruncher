from dataclasses import dataclass


@dataclass
class LigandStats:
    """
    Dataclass holding information about a ligand.
    """
    heavy_atom_count: int
    flexibility: float
