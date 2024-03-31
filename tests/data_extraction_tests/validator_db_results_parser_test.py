import pytest

from src.generic_file_handlers.json_file_loader import load_json_file
from src.data_extraction.validator_db_result_parser import parse_validator_db_result
from tests.test_constants import *
from tests.utils import compare_dataclasses
from tests.expected_results_loader import load_expected_validator_db_protein_data


@pytest.mark.parametrize("pdb_id", TEST_PDB_IDS)
def test_parse_validator_db_result_basic(pdb_id: str):
    # arrange
    path_to_result_json = path.join(TEST_DATA_PATH, pdb_id, "result.json")
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
