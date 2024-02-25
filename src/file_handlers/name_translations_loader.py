import logging

from src.file_handlers.json_file_loader import load_json_file
from src.exception import ParsingError


def load_familiar_names_translation(filepath: str) -> dict[str, str]:
    """
    Loads name translations from factor name into familiar name as a dictionary.
    :param filepath: Path to the name translations json.
    :return: Dictionary with keys as original factor names, and values as their translation into familiar names.
    :raises ParsingError: In case of file or json error.
    """
    try:
        loaded_json = load_json_file(filepath)
        result = {}
        for names_item in loaded_json:
            id_name = names_item.get("ID")
            familiar_name = names_item.get("FamiliarName")
            if id_name is None or familiar_name is None:
                logging.warning(
                    "[loading names translations] Found item where one or both items (ID, FamiliarName) are "
                    "not present. Skipped it. Item: %s",
                    names_item
                )
                continue
            result[id_name] = familiar_name
        return result
    except ParsingError as ex:
        raise ParsingError("Failed to load names translation") from ex
