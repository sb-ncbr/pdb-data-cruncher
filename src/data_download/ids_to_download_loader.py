import logging
from typing import Optional

from src.exception import ParsingError
from src.generic_file_handlers.json_file_loader import load_json_file
from src.models.ids_to_update import ChangedIds


def load_overriden_ids_to_download(filepath: str) -> Optional[ChangedIds]:
    """
    Load ids to download from file.
    :param filepath:
    :return: Changed ids (updated holds loaded ids, deleted is empty).
    """
    updated_ids = _load_ids_to_download(filepath)
    if updated_ids is None:
        return None
    logging.info("Override for ids to download was set, will update structures: %s", updated_ids)
    return ChangedIds(
        updated=updated_ids,
        deleted=[],
    )


def _load_ids_to_download(list_of_ids_path: str) -> Optional[list[str]]:
    try:
        ids_json = load_json_file(list_of_ids_path)
        if not isinstance(ids_json, list) or [item for item in ids_json if not isinstance(item, str)]:
            logging.error("Loaded json %s with ids to update is not a list of strings.", ids_json)
            return None
        return ids_json
    except ParsingError as ex:
        logging.error("Failed loading ids to download from json %s: %s", list_of_ids_path, ex)
        return None
