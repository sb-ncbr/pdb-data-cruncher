import logging
import os
from enum import Enum
from typing import Any

from src.data_download.http_request_handler import get_response_json
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
    VALIDATOR_DB = "validatorDB"


def download_one_type_rest_files(
    ids_to_download: set[str], rest_type: RestDataType, output_folder_path: str, single_request_timeout_s: int
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
            if rest_type == RestDataType.VALIDATOR_DB:
                _check_vdb_data_downloaded(rest_json)
            _save_rest_json(rest_json, output_folder_path, rest_type, structure_id)
        except (DataDownloadError, FileWritingError) as ex:
            logging.info("Failed to download %s rest json for %s. Reason: %s.", rest_type.value, structure_id, ex)
            failed_ids.append(structure_id)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.error(
                "Unexpected error: %s. Failed to download %s rest json for %s.", ex, rest_type.value, structure_id
            )
            failed_ids.append(structure_id)

    if len(failed_ids) > 0:
        successful_count = len(ids_to_download) - len(failed_ids)
        logging.info(
            "Finished %s rest download. Successful: %s. Failed: %s.", rest_type.value, successful_count, len(failed_ids)
        )
    else:
        logging.info("Successfully finished %s rest download for all ids.", rest_type.value)

    return failed_ids


def _download_one_type_rest_file(structure_id: str, rest_type: RestDataType, single_request_timeout_s: int) -> Any:
    """
    Download one file from rest api for given rest type. The address is assembled based on the rest type.
    :param structure_id:
    :param rest_type:
    :param single_request_timeout_s:
    :return:
    """
    address = _get_rest_data_address(structure_id, rest_type)
    logging.debug("Downloading %s rest json for id %s from %s", rest_type.value, structure_id, address)
    return get_response_json(address, get_timeout_s=single_request_timeout_s, retry_attempts=2)


def _check_vdb_data_downloaded(rest_json: dict) -> None:
    """
    Check if the response contains actual validator db report. If it is empty, raise DataDownloadError.
    :param rest_json:
    :raises DataDownloadError: If the response has no version, which happens when there is no report ready yet.
    """
    if rest_json.get("Version") in [None, "n/a"]:
        raise DataDownloadError("Validator DB has no data for this structure.")


def _save_rest_json(rest_json: Any, output_folder_path: str, rest_type: RestDataType, structure_id: str) -> None:
    """
    Save given rest response into file. The location depends on the rest type given.
    :param rest_json:
    :param output_folder_path:
    :param rest_type:
    :param structure_id:
    """
    if rest_type == RestDataType.VALIDATOR_DB:
        _save_validator_db_json(rest_json, output_folder_path, structure_id)
    else:
        _save_pdbe_rest_json(rest_json, output_folder_path, rest_type, structure_id)


def _save_validator_db_json(rest_json: Any, output_folder_path: str, structure_id: str) -> None:
    """
    Save given validator db response into a file.
    :param rest_json:
    :param output_folder_path:
    :param structure_id:
    """
    directory_path = os.path.join(output_folder_path, structure_id)
    filepath = os.path.join(directory_path, "result.json")

    if not os.path.exists(directory_path):
        os.mkdir(directory_path)

    write_json_file(filepath, rest_json)


def _save_pdbe_rest_json(rest_json: Any, output_folder_path: str, rest_type: RestDataType, structure_id: str) -> None:
    """
    Save rest json into file, for rest_type that corresponds with pdbe data source
    (assembly, summary, molecules, (related) publications).
    :param rest_json:
    :param output_folder_path:
    :param rest_type:
    :param structure_id:
    """
    filepath = os.path.join(output_folder_path, rest_type.value, f"{structure_id}.json")
    write_json_file(filepath, rest_json)


def _get_rest_data_address(structure_id: str, rest_data_type: RestDataType) -> str:
    """
    Assemble address for given structure id, respecting the different rest data type given.
    :param structure_id:
    :param rest_data_type:
    :return: Address of data as string.
    """
    if rest_data_type == RestDataType.VALIDATOR_DB:
        return f"https://webchem.ncbr.muni.cz/Platform/ValidatorDb/Data/{structure_id}?source=ByStructure"
    return f"https://www.ebi.ac.uk/pdbe/api/pdb/entry/{rest_data_type.value}/{structure_id}"
