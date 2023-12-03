import json
import logging

import requests

from src.exception import DataDownloadError


def get_and_store_json(address: str, new_file_path: str, get_timeout_s: int) -> None:
    """
    Runs GET request on given address and saves the response content into given location.
    :param address: Endpoint to get.
    :param new_file_path: Path where the new file will be saved.
    :param get_timeout_s: Timeout for GET request in seconds.
    :return: True if succeeded, False otherwise.
    :raises DataDownloadError: If the download itself or saving the response fails.
    """
    response_json = get_response_json(address, get_timeout_s)
    save_json_into_file(response_json, new_file_path)
    logging.debug("Contents of %s saved into %s", address, new_file_path)


def get_response_json(address: str, get_timeout_s: int) -> dict:
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
            raise DataDownloadError(f"GET {address} failed with status code {response.status_code}, "
                                    f"content '{response.content}'.")
        return response.json()
    except requests.exceptions.RequestException as ex:
        raise DataDownloadError(f"GET {address} failed. {ex}") from ex
    except requests.exceptions.JSONDecodeError as ex:
        raise DataDownloadError(f"JSONDecodeError from request to {address}. {ex}") from ex


def save_json_into_file(json_content: dict, new_file_path: str) -> None:
    """
    Takes given json content and saves it into file with given file path.
    :param json_content: Json content to save into the file.
    :param new_file_path: Path including the name of new file.
    :raises DataDownloadError: If the path doesn't exist or the file writing fails.
    """
    json_object = json.dumps(json_content, indent=2)
    try:
        with open(new_file_path, "w", encoding="utf8") as outfile:
            outfile.write(json_object)
    except OSError as ex:
        raise DataDownloadError(f"Failed to open new file location '{new_file_path}' for writing. {ex}") from ex
