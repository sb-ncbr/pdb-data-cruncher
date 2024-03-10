import logging

from src.file_handlers.json_file_loader import load_json_file
from src.models import FactorType
from src.utils import get_factor_type


def load_factor_names_translations(filepath: str) -> dict[str, str]:
    """
    Loads name translations from factor name into familiar name as a dictionary where key is string.
    :param filepath: Path to the name translations json.
    :return: Dictionary with keys as original factor names, and values as their translation into familiar names.
    :raises ParsingError: In case of file or json error.
    """
    loaded_json = load_json_file(filepath)
    result = {}
    for names_item in loaded_json:
        id_name = names_item.get("ID")
        familiar_name = names_item.get("FamiliarName")
        if id_name is None or familiar_name is None:
            logging.warning(
                "[loading names translations] Found item where one or both items (ID, FamiliarName) are "
                "not present. Skipped it. Item: %s",
                names_item,
            )
            continue
        result[id_name] = familiar_name
    return result


def load_factor_type_names_translations(filepath: str) -> dict[FactorType, str]:
    """
    Loads name translations from factor name into familiar name as a dictionary where key is FactorType.
    :param filepath: Path to the name translations json.
    :return: Dictionary with keys as FactorType, and values as their translation into familiar names.
    :raises ParsingError: In case of file or json error.
    """
    loaded_json = load_json_file(filepath)
    result = {}
    for names_item in loaded_json:
        id_name = names_item.get("ID")
        familiar_name = names_item.get("FamiliarName")
        if id_name is None or familiar_name is None:
            logging.warning(
                "[loading names translations] Found item where one or both items (ID, FamiliarName) are "
                "not present. Skipped it. Item: %s",
                names_item,
            )
            continue
        factor_type = get_factor_type(id_name)
        if factor_type:
            result[factor_type] = familiar_name
        else:
            logging.warning("Factor with name %s failed to be transformed into factor type.", id_name)
    return result
