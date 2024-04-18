from dataclasses import dataclass, field


@dataclass(slots=True)
class IdsToUpdateAndRemove:
    """
    Class holding lists of structure and ligand id to update/remove during data extraction or donwload phase.
    """

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

    def to_dict(self) -> dict[str, list[str]]:
        """
        Return dictionary representation for storing as a json.
        """
        return {
            "structuresToUpdate": self.structures_to_update,
            "structuresToDelete": self.structures_to_delete,
            "ligandsToUpdate": self.ligands_to_update,
            "ligandsToDelete": self.ligands_to_delete,
        }

    @staticmethod
    def from_dict(ids_json) -> 'IdsToUpdateAndRemove':
        """
        Create instance from loaded json.
        :param ids_json:
        """
        return IdsToUpdateAndRemove(
            structures_to_update=ids_json["structuresToUpdate"],
            structures_to_delete=ids_json["structuresToDelete"],
            ligands_to_update=ids_json["ligandsToUpdate"],
            ligands_to_delete=ids_json["ligandsToDelete"],
        )


@dataclass
class ChangedIds:
    """
    Class holding lists of updated and deleted ids.
    """

    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
