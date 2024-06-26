from enum import Enum


class FailedIdsSourceType(Enum):
    """
    Enum holding type for data source and their name for retrieving/storing information about failing ids.
    """

    REST_ASSEMBLY = "RestAssembly"
    REST_MOLECULES = "RestMolecules"
    REST_PUBLICATIONS = "RestPublications"
    REST_RELATED_PUBLICATIONS = "RestRelatedPublications"
    REST_SUMMARY = "RestSummary"
    VALIDATOR_DB_REPORT = "ValidatorDbReport"


def get_failing_ids(failed_ids_json: dict, data_type: FailedIdsSourceType) -> list[str]:
    """
    Get list of failing ids from last time concerning given data type.
    :param failed_ids_json:
    :param data_type:
    :return: List of strings representing failed ids.
    """
    return list(failed_ids_json.get(data_type.value, {}).keys())


def update_failing_ids(
    failed_ids_json: dict, data_type: FailedIdsSourceType, failed_ids: list[str]
) -> None:
    """
    Update failing ids json for given data type and given failed ids. Entries with ids that are not present in failed
    ids this time are removed from the json as well. Pass empty failed ids to remove all.
    :param failed_ids_json: Loaded json with failing ids from download json.
    :param data_type: Type of data to update.
    :param failed_ids: List of ids that failed this time.
    """
    updated_id_group = {}

    for failed_id in failed_ids:
        failed_count = failed_ids_json.get(data_type.value, {}).get(failed_id, 0)
        failed_count += 1
        updated_id_group[failed_id] = failed_count

    failed_ids_json[data_type.value] = updated_id_group
