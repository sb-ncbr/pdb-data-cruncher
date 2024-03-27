from typing import Any

from src.exception import DataTransformationError


def update_versions_json(versions_json: list, current_date_string: str) -> None:
    """
    Update versions json to include this run's information and remove the last one.
    :param versions_json:
    :param current_date_string: String representing date in format 20240101.
    """
    if not isinstance(versions_json, list) or len(versions_json) == 0:
        raise DataTransformationError("Root element of given versions json is not a list or is empty.")

    _check_first_element_can_be_removed(versions_json[0])
    versions_json.pop(0)
    todays_element = _construct_todays_element(current_date_string)
    versions_json.insert(0, todays_element)


def _check_first_element_can_be_removed(versions_item: dict[str, Any]) -> None:
    try:
        if "current" not in versions_item["userFriendlyName"]:
            raise DataTransformationError(
                f"Unexpected format of first item in old versions json, cannot proceed. Json: {versions_item}"
            )
    except (TypeError, ValueError) as ex:
        raise DataTransformationError(
            f"Unexpected format of first item in old versions json, cannot proceed. Json: {versions_item}"
        ) from ex


def _construct_todays_element(current_date_string: str) -> dict[str, Any]:
    if len(current_date_string) != 8:
        raise DataTransformationError(
            f"Unexpected date string recieved ('{current_date_string}'), expected format: 20240101."
        )

    return {
        "id": current_date_string,
        "default": True,
        "userFriendlyName": f"current {current_date_string[:4]}-{current_date_string[4:6]}-{current_date_string[6:]}",
    }
