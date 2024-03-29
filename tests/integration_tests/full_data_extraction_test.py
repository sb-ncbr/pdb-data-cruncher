import pytest

from src.config import Config
from src.data_extraction.parsing_manger import ParsingManger
from tests.test_constants import *
from tests.expected_results_loader import load_row_of_csv_as_dict
from tests.utils import strings_are_equal_respecting_floats, Differences, Difference


@pytest.mark.integration
@pytest.mark.parametrize("pdb_id", TEST_PDB_IDS)
def test_full_data_extraction_basic(pdb_id: str):
    # arrange
    expected_csv_row_dict = load_row_of_csv_as_dict(pdb_id)
    config = Config()
    config.filepaths.dataset_root_path = TEST_DATA_PATH
    config.filepaths._rest_jsons_name = pdb_id
    config.filepaths._pdb_mmcifs_name = pdb_id
    config.filepaths._xml_reports_name = pdb_id
    config.filepaths._validator_db_results_name = ""
    config.filepaths._ligand_stats_name = "ligandStats.csv"

    # act
    complete_protein_data = ParsingManger.load_all_protein_data(pdb_id, config)
    assert complete_protein_data is not None
    protein_data_as_csv_row_dict = complete_protein_data.as_dict_for_csv()

    # assert
    differences = compare_csv_row_dicts(protein_data_as_csv_row_dict, expected_csv_row_dict)
    assert not differences.count, differences.get_difference_description()
    # finally, check the number of extracted and compared csv values is the same as expected csv columns
    # if it weren't, it means error in dictionaries that translate protein data fields to resulting csv rows
    assert set(expected_csv_row_dict.keys()) == set(protein_data_as_csv_row_dict.keys())


def compare_csv_row_dicts(actual: dict[str, str], expected: dict[str, str]) -> Differences:
    """
    Compares all items in given dicts with string values. If the strings represent float values,
    it also tries to compare them as float values.
    :param actual: Dict representing actual result.
    :param expected: Dict representing expected result.
    :return: Found differences object.
    """
    differences = Differences()
    if len(actual) != len(expected):
        differences.items.append(Difference("list length", len(expected), len(actual)))

    for expected_key, expected_value in expected.items():
        actual_value = actual.get(expected_key)
        if not strings_are_equal_respecting_floats(actual_value, expected_value):
            differences.items.append(Difference(expected_key, expected_value, actual_value))

    return differences
