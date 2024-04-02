from typing import Optional

from src.models.ids_to_update import IdsToUpdateAndRemove
from src.models.protein_data import ProteinDataComplete


def update_structures_to_update_based_on_ligand_occurence(
    ids_to_update: IdsToUpdateAndRemove, ligand_occurrence_json: dict[str, list[str]]
) -> None:
    """
    If any ids for ligands changed, look into ligand occurence json if any pdb_ids are using them and if so,
    add those ids to the ids to be updated.
    :param ids_to_update:
    :param ligand_occurrence_json:
    """
    if len(ids_to_update.ligands_to_update) == 0 and len(ids_to_update.ligands_to_delete) == 0:
        return

    for structure_id, list_of_ligands in ligand_occurrence_json.items():
        if structure_id in ids_to_update.structures_to_update or structure_id in ids_to_update.structures_to_delete:
            continue  # will be changed anyway

        for ligand_id in list_of_ligands:
            if ligand_id in ids_to_update.ligands_to_update or ligand_id in ids_to_update.ligands_to_delete:
                ids_to_update.structures_to_update.append(structure_id)
                continue


def update_ligand_occurrence_in_structures(
    protein_data_list: list[ProteinDataComplete], ligand_occurrence_json: dict[str, list[str]]
) -> None:
    """
    Add structure's ligands to the json structure.
    :param protein_data_list: List of complete protein data instances.
    :param ligand_occurrence_json:
    :return:
    """
    for protein_data in protein_data_list:
        if protein_data.pdbx and len(protein_data.pdbx.ligand_types_present) > 0:
            ligand_occurrence_json[protein_data.pdb_id] = list(protein_data.pdbx.ligand_types_present)


def remove_structure_from_ligand_occurrence(
    structure_id: str, ligand_occurrence_json: dict[str, list[str]]
) -> None:
    """
    Remove structure from ligand occurence json.
    :param structure_id: ID of structure (PDB ID).
    :param ligand_occurrence_json: Json with ligand occurence data.
    """
    ligand_occurrence_json.pop(structure_id)
