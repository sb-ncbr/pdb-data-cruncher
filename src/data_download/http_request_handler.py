import logging

import requests

from src.exception import DataDownloadError


def get_response_json(address: str, get_timeout_s: int, retry_attempts: int = 0) -> dict:
    """
    Make a request to given address, check status code and return json in response.
    :param address: Full endpoint address.
    :param get_timeout_s: Timeout for GET request in seconds.
    :param retry_attempts: Times to retry.
    :return: Response as json.
    :raises DataDownloadError: If the response isn't status code 200 or if the content isn't json.
    """
    attempt_number = 0
    last_exception = None

    while attempt_number <= retry_attempts:
        try:
            return get_response(address, get_timeout_s).json()
        except DataDownloadError as ex:
            logging.info("Download attempt #%s failed. %s", attempt_number + 1, ex)
            last_exception = ex
        attempt_number += 1

    raise last_exception


def get_response(address: str, get_timeout_s: int) -> requests.Response:
    """
    Make a request to given address, check status code and return its response.
    :param address: Full endpoint address.
    :param get_timeout_s: Timeout for GET request in seconds.
    :return: Response object.
    :raises DataDownloadError: If the response isn't status code 200 or other error.
    """
    try:
        response = requests.get(address, timeout=get_timeout_s)
        if response.status_code != 200:
            raise DataDownloadError(
                f"GET {address} failed with status code {response.status_code}, content '{response.content}'."
            )
        return response
    except requests.exceptions.RequestException as ex:
        raise DataDownloadError(f"GET {address} failed.") from ex

