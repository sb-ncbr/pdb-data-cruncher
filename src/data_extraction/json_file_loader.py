import json
from typing import Any

from src.exception import ParsingError


def load_json_file(path_to_file: str) -> Any:
    """
    Loads file as json with encoding utf-8, and returns it.
    :param path_to_file: Path to file that should be loaded.
    :return: Loaded json.
    :raises ParsingError: In case of file error or json decoding error.
    """
    try:
        with open(path_to_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as ex:
        raise ParsingError(str(ex)) from ex
