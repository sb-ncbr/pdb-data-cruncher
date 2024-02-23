import pytest

from src.data_extraction.json_file_loader import load_json_file
from src.data_extraction.validator_db_result_parser import parse_validator_db_result
from tests.test_constants import *
from tests.utils import compare_dataclasses
from tests.expected_results_loader import load_expected_validator_db_protein_data


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_validator_db_result_basic(pdb_id: str):
    unified_test_parse_validator_db_result(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_validator_db_result_extended(pdb_id: str):
    unified_test_parse_validator_db_result(pdb_id, True)


def unified_test_parse_validator_db_result(pdb_id: str, extended: bool = False):
    # arrange
    test_data_root = EXTENDED_TEST_DATA_PATH if extended else BASIC_TEST_DATA_PATH
    path_to_result_json = path.join(test_data_root, pdb_id, "result.json")
    expected_protein_data = load_expected_validator_db_protein_data(pdb_id)

    # act
    result_json = load_json_file(path_to_result_json)
    actual_protein_data = parse_validator_db_result(pdb_id, result_json)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(
        actual_protein_data,
        expected_protein_data,
    )
    assert not differences.count, differences.get_difference_description()
