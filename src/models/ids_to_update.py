from dataclasses import dataclass, field


@dataclass(slots=True)
class IdsToUpdateAndRemove:
    structures_to_update: list[str] = field(default_factory=list)
    structures_to_delete: list[str] = field(default_factory=list)
    ligands_to_update: list[str] = field(default_factory=list)
    ligands_to_delete: list[str] = field(default_factory=list)

    def validate(self) -> None:
        """
        Checks no item is present in both to update and to delete lists.
        :raises ValueError: When item is present in both to_update and to_delete lists
        """
        for item in self.structures_to_update:
            if item in self.structures_to_delete:
                raise ValueError(f"Structure {item} was present in both list to update and list to delete.")

        for item in self.ligands_to_update:
            if item in self.ligands_to_delete:
                raise ValueError(f"Ligand {item} was present in both list to update and list to delete.")
