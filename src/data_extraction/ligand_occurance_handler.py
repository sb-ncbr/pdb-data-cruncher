from typing import Any, Optional

from src.models.protein_data import ProteinDataComplete


def update_ligand_occurence_in_structures(
    protein_data_list: list[ProteinDataComplete], ligand_occurence_json: dict[str, list[str]]
) -> None:
    """
    For given protein data loaded with ligand type names found inside them, it updates the ligand occurence json so
    that each structure's id is present in a list under key representing the ligand name. If the structure id was
    present in other ligand type before, but not now, it is removed from under that key.
    :param protein_data_list: List of complete protein data instances.
    :param ligand_occurence_json:
    :return:
    """
    for protein_data in protein_data_list:
        # clear this structure from any ligand entries that used to be used in it but not anymore
        remove_structure_from_ligand_occurence(
            protein_data.pdb_id, ligand_occurence_json, protein_data.pdbx.ligand_types_present
        )

        for ligand_name in protein_data.pdbx.ligand_types_present:
            if ligand_name not in ligand_occurence_json.keys():
                # ligand is not present at all, create the entry
                ligand_occurence_json[ligand_name] = [protein_data.pdb_id]
            elif protein_data.pdb_id not in ligand_occurence_json[ligand_name]:
                # ligand has entry, but this structure is not in it yet
                ligand_occurence_json[ligand_name].append(protein_data.pdb_id)


def remove_structure_from_ligand_occurence(
    structure_id: str, ligand_occurence_json: dict[str, list[str]], exclusions_to_keep: Optional[set[str]] = None
) -> None:
    """
    Remove structure from every entry in ligand occurence json it is in. If any ligand entry is empty afterwards,
    remove it too.
    :param structure_id: ID of structure (PDB ID).
    :param ligand_occurence_json: Json with ligand occurence data.
    :param exclusions_to_keep: List of ligand ids in which the structure should remain.
    """
    if not exclusions_to_keep:
        exclusions_to_keep = set()

    ligand_ids_to_remove = []
    for ligand_id, structure_id_list in ligand_occurence_json.items():
        if ligand_id in exclusions_to_keep:
            continue

        if structure_id in structure_id_list:
            structure_id_list.remove(structure_id)
        if len(structure_id_list) == 0:
            ligand_ids_to_remove.append(ligand_id)

    for ligand_id in ligand_ids_to_remove:
        ligand_occurence_json.pop(ligand_id)
