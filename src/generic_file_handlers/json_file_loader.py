import json
from typing import Any

from src.exception import ParsingError


def load_json_file(path_to_file: str, raise_on_file_not_found: bool = True, default_if_not_found: Any = None) -> Any:
    """
    Loads file as json with encoding utf-8, and returns it.
    :param path_to_file: Path to file that should be loaded.
    :param raise_on_file_not_found: Default True. If set to false, default_if_not_found is returned on file not
    found instead.
    :param default_if_not_found: If set, will be returned in case of FileNotFound instead of exception.
    :return: Loaded json.
    :raises ParsingError: In case of file error or json decoding error.
    """
    try:
        with open(path_to_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as ex:
        if not raise_on_file_not_found:
            return default_if_not_found
        raise ParsingError(str(ex)) from ex
    except (OSError, json.JSONDecodeError) as ex:
        raise ParsingError(str(ex)) from ex
