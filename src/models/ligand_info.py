from dataclasses import dataclass


@dataclass(slots=True)
class LigandInfo:
    """
    Dataclass holding information about a ligand.
    """

    id: str
    heavy_atom_count: int
    flexibility: float

    def as_dict(self) -> dict[str, str]:
        """
        Transform self data into dictionary.
        """
        return {
            "LigandID": self.id,
            "heavyAtomSize": str(self.heavy_atom_count),
            "flexibility": str(round(self.flexibility, 6))
        }
