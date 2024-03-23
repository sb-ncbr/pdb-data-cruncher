from typing import Any

from src.exception import DataTransformationError
from src.utils import get_formatted_date


def update_versions_json(versions_json: list) -> None:
    if not isinstance(versions_json, list) or len(versions_json) == 0:
        raise DataTransformationError("Root element of given versions json is not a list or is empty.")

    _check_first_element_can_be_removed(versions_json[0])
    versions_json.pop(0)
    todays_element = _construct_todays_element()
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


def _construct_todays_element() -> dict[str, Any]:
    return {
        "id": get_formatted_date(),
        "default": True,
        "userFriendlyName": f"current {get_formatted_date('-')}"
    }
