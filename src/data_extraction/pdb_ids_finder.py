import logging
from enum import Enum

from src.config import Config
from src.generic_file_handlers.plain_text_loader import load_text_file_as_lines
from src.exception import ParsingError
from src.utils import find_matching_files


class Purpose(Enum):
    """
    Purpose for which the ids are being searched for. Only used in this file.
    """

    UPDATE = 1
    REMOVAL = 2


def find_pdb_ids_to_update(config: Config) -> list[str]:
    """
    Depending on configuration, load pdb ids to process from appropriate source. From env variable, if set.
    From file specified in env variable, if set. From all files, if force complete data extraction is set.
    From last download run logs otherwise. Checks there is at least one id present, and that every id is
    only alphanum char and has at least 4 chars.
    :param config: App configuration.
    :return: List of strings.
    """
    pdb_ids_to_update = _find_pdb_ids(config, Purpose.UPDATE)
    logging.info("Found these PDB IDS to be extacted and updated in crunched csv: %s", pdb_ids_to_update)
    return pdb_ids_to_update


def find_pdb_ids_to_remove(config: Config) -> list[str]:
    """
    Depending on configuration, load pdb ids to delete from data from appropriate source. From env variable, if set.
    From file specified in env variable, if set. Empty, if force complete data extraction is set.
    From last download run logs otherwise. Checks there is at least one id present, and that every id is
    only alphanum char and has at least 4 chars.
    :param config: App configuration.
    :return: List of strings.
    """
    pdb_ids_to_remove = _find_pdb_ids(config, Purpose.REMOVAL)
    logging.info("Found these PDB IDS to be extacted and updated in crunched csv: %s", pdb_ids_to_remove)
    return pdb_ids_to_remove


def _find_pdb_ids(config: Config, purpose: Purpose) -> list[str]:
    pdb_ids = _find_pdb_ids_without_quality_check(config, purpose)

    invalid_pdb_ids = []
    for pdb_id in pdb_ids:
        if not pdb_id.isalnum():
            invalid_pdb_ids.append(pdb_id)
        if len(pdb_id) < 4:
            invalid_pdb_ids.append(pdb_id)

    if invalid_pdb_ids:
        raise ParsingError(
            "Invalid pdb ids found - cannot proceed. Every pdb id needs to consist only from alpha-numerical "
            f"characters and have at least 4 characters. Invalid pdb ids: {invalid_pdb_ids}"
        )

    return pdb_ids


def _find_pdb_ids_without_quality_check(config: Config, purpose: Purpose) -> list[str]:
    """
    Depending on configuration, load pdb ids to process from appropriate source. From env variable, if set.
    From file specified in env variable, if set. From all files, if force complete data extraction is set.
    From last download run logs otherwise.
    :param config: App configuration.
    :param purpose: Purpose of pdb ids to find.
    :return: List of strings.
    """
    # get all ids present for complete data extraction
    if config.force_complete_data_extraction:
        if purpose == purpose.UPDATE:
            return _get_all_pdb_ids_from_present_pdbx_files(config)
        if purpose == purpose.REMOVAL:
            return []

    if config.run_data_extraction_only and config.use_supplied_pdb_ids_instead:
        # if only a subset of pdb ids is specified
        return _get_pdb_ids_suplied_from_config(config, purpose)

    # if nothing else is specified, attempt to load ids that need redoing from data download logs
    return _get_pdb_ids_to_update_from_download_logs(config, purpose)


def _get_pdb_ids_suplied_from_config(config: Config, purpose: Purpose):
    if purpose == purpose.UPDATE:
        if config.pdb_ids_to_update:
            return config.pdb_ids_to_update
        if config.pdb_ids_to_update_filepath:
            return load_text_file_as_lines(config.pdb_ids_to_update_filepath)
    elif purpose == purpose.REMOVAL:
        if config.pdb_ids_to_remove:
            return config.pdb_ids_to_remove
        if config.pdb_ids_to_update_filepath:
            return load_text_file_as_lines(config.pdb_ids_to_remove_filepath)
    return []  # in manual pdb feed, this purpose may not be specified and thus is empty


def _get_all_pdb_ids_from_present_pdbx_files(config: Config) -> list[str]:
    pdbx_filenames = find_matching_files(config.filepaths.pdb_mmcifs, ".cif")
    return [pdbx_filename.replace(".cif", "") for pdbx_filename in pdbx_filenames]


def _get_pdb_ids_to_update_from_download_logs(config: Config, purpose: Purpose) -> list[str]:
    # TODO potentially move to standalone file
    # get pdb ids that changed from download logs
    # get ligand ids that changed and cross referencing pdbstructure-ligand file, find extra ids to update
    raise NotImplementedError()
