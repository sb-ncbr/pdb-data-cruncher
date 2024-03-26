import logging
from typing import Any
from os import path
from enum import Enum

from src.generic_file_handlers.json_file_writer import write_json_file


class VersionsType(Enum):
    VERSIONS = "Versions"
    KEY_TRENDS_VERSIONS = "VersionsKT"


def create_versions_file(versions_json: Any, versions_type: VersionsType, output_folder_path: str) -> None:
    """
    Write factor hierarchy json into a file.
    :param versions_json: Json with content to write.
    :param versions_type: Type of version file.
    :param output_folder_path:
    """
    filepath = path.join(output_folder_path, f"{versions_type.value}.json")
    write_json_file(filepath, versions_json)
    logging.info("Saved updated versions file json into %s.", filepath)
