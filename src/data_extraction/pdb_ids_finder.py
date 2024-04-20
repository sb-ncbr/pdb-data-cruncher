import logging

from src.config import Config
from src.exception import ParsingError
from src.models.ids_to_update import IdsToUpdateAndRemove
from src.utils import find_matching_files
from src.generic_file_handlers.json_file_loader import load_json_file


def finds_ids_to_update_and_remove(config: Config) -> IdsToUpdateAndRemove:
    """
    Get structure and ligand ids to update and remove. By default, these are taken from download data logs that
    say what has changed. But if config has set path to ids to update and remove, that file is used instead.
    :param config: Application config.
    :raises ParsingError:
    """
    ids = _find_ids_to_update_and_remove(config)
    logging.debug("Will run data extraction with these ids to update and remove: %s", ids)
    return ids


def _find_ids_to_update_and_remove(config: Config) -> IdsToUpdateAndRemove:
    if config.force_complete_data_extraction:
        logging.info("Forced to run full data extraction by config. This will take a significantly longer.")
        return IdsToUpdateAndRemove(
            structures_to_update=_get_all_structure_ids_from_present_pdbx_files(config),
            structures_to_delete=[],
            ligands_to_update=_get_all_ligand_ids_from_present_pdbx_files(config),
            ligands_to_delete=[],
        )

    if (
        config.run_zipping_files_only or config.run_data_extraction_only
    ) and config.ids_to_remove_and_update_override_filepath:
        logging.info(
            "By passing IDS_TO_REMOVE_AND_UPDATE_OVERRIDE_PATH, structure and ligand ids will be fetched "
            "from %s instead of from old download logs.",
            config.ids_to_remove_and_update_override_filepath
        )
        return _load_ids_to_update_and_remove_from_json(config.ids_to_remove_and_update_override_filepath)

    return _load_ids_to_update_and_remove_from_json(config.filepaths.download_changed_ids_json)


def _load_ids_to_update_and_remove_from_json(json_filepath: str) -> IdsToUpdateAndRemove:
    try:
        ids_json = load_json_file(json_filepath)
    except ParsingError as ex:
        raise ParsingError(f"Failed to load ids to update and remove. Data extraction cannot proceed. {ex}") from ex

    try:
        return IdsToUpdateAndRemove.from_dict(ids_json)
    except ValueError as ex:
        raise ParsingError(f"Failed to load json with ids to update and remove: No item {ex}") from ex


def _get_all_structure_ids_from_present_pdbx_files(config: Config) -> list[str]:
    pdbx_filenames = find_matching_files(config.filepaths.pdb_mmcifs, ".cif")
    return [pdbx_filename.replace(".cif", "") for pdbx_filename in pdbx_filenames]


def _get_all_ligand_ids_from_present_pdbx_files(config: Config) -> list[str]:
    ligand_filenames = find_matching_files(config.filepaths.ligand_cifs, ".cif")
    return [ligand_filename.replace(".cif", "") for ligand_filename in ligand_filenames]
