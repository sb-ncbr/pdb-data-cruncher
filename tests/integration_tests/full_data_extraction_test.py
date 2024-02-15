import pytest

from src.config import Config
from src.data_extraction.parsing_manger import ParsingManger
from tests.test_constants import *
from tests.expected_results_loader import load_row_of_csv_ordered, count_expected_crunched_csv_columns
from tests.utils import compare_lists_of_string_with_float_imprecision


@pytest.mark.basic
@pytest.mark.integration
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_full_data_extraction_basic(pdb_id: str):
    unified_test_full_data_extraction(pdb_id)


@pytest.mark.extended
@pytest.mark.integration
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_full_data_extraction_extended(pdb_id: str):
    unified_test_full_data_extraction(pdb_id, True)


def unified_test_full_data_extraction(pdb_id: str, extended: bool = False):
    # arrange
    expected_csv_row = load_row_of_csv_ordered(pdb_id)
    expected_values_count = count_expected_crunched_csv_columns()
    test_data_root_path = EXTENDED_TEST_DATA_PATH if extended else BASIC_TEST_DATA_PATH
    config = Config(
        path_to_rest_jsons=(path.join(test_data_root_path, pdb_id)),
        path_to_pdbx_files=(path.join(test_data_root_path, pdb_id)),
        path_to_xml_reports=(path.join(test_data_root_path, pdb_id)),
        path_to_validator_db_results=test_data_root_path,
        path_to_ligand_stats_csv=(path.join(TEST_DATA_PATH, "ligandStats.csv")),
    )

    # act
    complete_protein_data = ParsingManger.load_all_protein_data(pdb_id, config)
    assert complete_protein_data is not None
    protein_data_as_csv_row = complete_protein_data.as_row_for_csv()

    # assert
    differences = compare_lists_of_string_with_float_imprecision(protein_data_as_csv_row, expected_csv_row)
    assert not differences.count, differences.get_difference_description()
    # finally, check the number of extracted and compared csv values is the same as expected csv columns
    # if it weren't, it means error in dictionaries that translate protein data fields to resulting csv rows
    assert len(protein_data_as_csv_row) == expected_values_count
