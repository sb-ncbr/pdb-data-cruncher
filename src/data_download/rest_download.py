import logging
from enum import Enum
from os import path
from typing import Any

import requests

from src.exception import DataDownloadError, FileWritingError
from src.generic_file_handlers.json_file_writer import write_json_file


class RestDataType(Enum):
    """
    Enum for rest data type, with value correspoinding to the rest endpoint name.
    Also defines the folder in which they are stored.
    """

    SUMMARY = "summary"
    MOLECULES = "molecules"
    ASSEMBLY = "assembly"
    PUBLICATIONS = "publications"
    RELATED_PUBLICATIONS = "related_publications"


def download_one_type_rest_files(
    ids_to_download: list[str], rest_type: RestDataType, output_folder_path: str, single_request_timeout_s: int
) -> list[str]:
    """
    Download rest files for given rest type and given list of ids. Store them as jsons in given folder.
    :param ids_to_download:
    :param rest_type:
    :param output_folder_path: Path where to store all the rest files (no matter then type).
    :param single_request_timeout_s:
    :return: List of failed ids.
    """
    logging.info(
        "Starting download for %s rest files. Will attempt to download %s files.",
        rest_type.value,
        len(ids_to_download)
    )
    failed_ids = []

    for structure_id in ids_to_download:
        try:
            rest_json = _download_one_type_rest_file(structure_id, rest_type, single_request_timeout_s)
            rest_filepath = path.join(output_folder_path, rest_type.value, f"{structure_id}.json")
            write_json_file(rest_filepath, rest_json)
        except (DataDownloadError, FileWritingError) as ex:
            logging.warning("Failed to download %s rest json for %s. Reason: %s.", rest_type.value, structure_id, ex)
            failed_ids.append(structure_id)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.error(
                "Unexpected error: %s. Failed to download %s rest json for %s.", ex, rest_type.value, structure_id
            )
            failed_ids.append(structure_id)

    if len(failed_ids) > 0:
        successful_count = len(ids_to_download) - len(failed_ids)
        logging.warning(
            "Finished %s rest download. Successful: %s. Failed: %s.", rest_type.value, successful_count, len(failed_ids)
        )
    else:
        logging.info("Successfully finished %s rest download for all ids.", rest_type.value)

    return failed_ids


def _download_one_type_rest_file(structure_id: str, rest_type: RestDataType, single_request_timeout_s: int) -> Any:
    address = _get_rest_data_address(structure_id, rest_type)
    logging.debug("Downloading %s rest json for id %s from %s", rest_type.value, structure_id, address)
    return _get_response_json(address, single_request_timeout_s)


def _get_rest_data_address(structure_id: str, rest_data_type: RestDataType) -> str:
    return f"https://www.ebi.ac.uk/pdbe/api/pdb/entry/{rest_data_type.value}/{structure_id}"


def _get_response_json(address: str, get_timeout_s: int) -> dict:
    """
    Make a request to given address, check status code and return json in response.
    :param address: Full endpoint address.
    :param get_timeout_s: Timeout for GET request in seconds.
    :return: Response as json.
    :raises DataDownloadError: If the response isn't status code 200 or if the content isn't json.
    """
    try:
        response = requests.get(address, timeout=get_timeout_s)
        if response.status_code != 200:
            raise DataDownloadError(
                f"GET {address} failed with status code {response.status_code}, content '{response.content}'."
            )
        return response.json()
    except requests.exceptions.RequestException as ex:
        raise DataDownloadError(f"GET {address} failed.") from ex
