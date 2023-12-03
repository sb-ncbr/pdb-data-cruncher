import json
from typing import Any

from src.exception import ParsingError


def load_json_file(path_to_file: str) -> Any:
    try:
        with open(path_to_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as ex:
        raise ParsingError(str(ex)) from ex
