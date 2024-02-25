import json
from typing import Any

from src.exception import FileWritingError


def write_json_file(path_to_file: str, json_to_write: Any) -> None:
    """
    Writes given json into file as json with encoding utf-8.
    :param path_to_file: Path to file that should be loaded.
    :param json_to_write: Json (list or dictionary) to write.
    :raises FileWritingError: In case of error with writing the file or fault with the json object.
    """
    try:
        with open(path_to_file, "w", encoding="utf-8") as f:
            json.dump(json_to_write, f, indent="\t")
    except (OSError, TypeError, ValueError) as ex:
        raise FileWritingError(f"Cannot create json file {path_to_file}.") from ex
