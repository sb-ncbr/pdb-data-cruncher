import logging

from src.config import Config
from src.generic_file_handlers.plain_text_loader import load_text_file_as_lines
from src.exception import ParsingError
from src.utils import find_matching_files


def find_pdb_ids_to_update(config: Config) -> list[str]:
    """
    Depending on configuration, load pdb ids to process from appropriate source. From env variable, if set.
    From file specified in env variable, if set. From all files, if force complete data extraction is set.
    From last download run logs otherwise. Checks there is at least one id present, and that every id is
    only alphanum char and has at least 4 chars.
    :param config: App configuration.
    :return: List of strings.
    """
    pdb_ids_to_update = _find_pdb_ids_to_update_without_quality_check(config)
    if len(pdb_ids_to_update) == 0:
        raise ParsingError("Found 0 pdb ids to update. Check the source of the data (env variable or download logs")

    invalid_pdb_ids = []
    for pdb_id in pdb_ids_to_update:
        if not pdb_id.isalnum():
            invalid_pdb_ids.append(pdb_id)
        if len(pdb_id) < 4:
            invalid_pdb_ids.append(pdb_id)

    if invalid_pdb_ids:
        raise ParsingError(
            "Invalid pdb ids found - cannot proceed. Every pdb id needs to consist only from alpha-numerical "
            f"characters and have at least 4 characters. Invalid pdb ids: {invalid_pdb_ids}"
        )

    logging.info("Found these PDB IDS to be extacted and updated in crunched csv: %s", pdb_ids_to_update)
    return pdb_ids_to_update


def _find_pdb_ids_to_update_without_quality_check(config: Config) -> list[str]:
    """
    Depending on configuration, load pdb ids to process from appropriate source. From env variable, if set.
    From file specified in env variable, if set. From all files, if force complete data extraction is set.
    From last download run logs otherwise.
    :param config: App configuration.
    :return: List of strings.
    """
    # get all ids present for complete data extraction
    if config.force_complete_data_extraction:
        return _get_all_pdb_ids_from_present_pdbx_files(config)

    if config.run_data_extraction_only:
        # if only a subset of pdb ids is specified
        if config.pdb_ids_to_update:
            return config.pdb_ids_to_update
        if config.pdb_ids_to_update_filepath:
            return load_text_file_as_lines(config.pdb_ids_to_update_filepath)

    # if nothing else is specified, attempt to load ids that need redoing from data download logs
    return _get_pdb_ids_to_update_from_download_logs(config)


def _get_all_pdb_ids_from_present_pdbx_files(config: Config) -> list[str]:
    pdbx_filenames = find_matching_files(config.filepaths.pdb_mmcifs, ".cif")
    return [pdbx_filename.replace(".cif", "") for pdbx_filename in pdbx_filenames]


def _get_pdb_ids_to_update_from_download_logs(config: Config) -> list[str]:
    # TODO potentially move to standalone file
    # get pdb ids that changed from download logs
    # get ligand ids that changed and cross referencing pdbstructure-ligand file, find extra ids to update
    raise NotImplementedError()
