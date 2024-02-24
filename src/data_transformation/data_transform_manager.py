import logging

from src.config import Config
from src.file_handlers.json_file_loader import load_json_file
from src.data_transformation.default_plot_data_creator import create_default_plot_settings
from src.exception import ParsingError, DataTransformationError


class DataTransformManager:
    """
    Class with only static methods aggregating functions around creating new files out of crunched data
    for the valtrends db backend.
    """

    @staticmethod
    def create_default_plot_settings(config: Config) -> None:
        familiar_names_translation = load_familiar_names_translation(config.familiar_name_translation_path)
        some_result = create_default_plot_settings(None, None, familiar_names_translation)
        pass


# TODO move to new file later
def load_familiar_names_translation(filepath: str) -> dict[str, str]:
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
        raise DataTransformationError("Failed to load names translation") from ex
