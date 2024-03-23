import pytest
from unittest.mock import patch, mock_open

from src.file_handlers.crunched_data_csv_writer import create_crunched_csv_file
from src.models import CRUNCHED_CSV_FACTOR_ORDER
from src.exception import IrrecoverableError
from tests.expected_results_loader import load_complete_protein_data
from tests.test_constants import TEST_PDB_IDS


def test_crunched_data_csv_gets_created_with_data():
    """
    Test checks:
    - whether open file with given path was called
    - whether the resulting csv has correct number of rows
    - whether the resulting csv has header loaded with all items in correct order
    - whether each protein row has good pdb_id value
    - whether each protein row has the correct number of items (data itself is not checked, that is covered by
    other tests enough)
    """
    # arrange
    all_pdb_ids = TEST_PDB_IDS
    protein_data = [load_complete_protein_data(pdb_id) for pdb_id in all_pdb_ids]
    dummy_path = "dummy_path"
    expected_header = ";".join(CRUNCHED_CSV_FACTOR_ORDER)

    with patch("builtins.open", mock_open()) as mock_write:
        # act
        protein_data_as_dicts = [data.as_dict_for_csv() for data in protein_data]
        create_crunched_csv_file(protein_data_as_dicts, dummy_path)

        # assert
        mock_write.assert_called_once_with(dummy_path, "w", encoding="utf8")
        write_calls_args = mock_write.return_value.write.call_args_list

        assert write_calls_args[0][0][0].strip() == expected_header.strip()  # csv header
        assert len(write_calls_args) == len(all_pdb_ids) + 1  # all ids have rows + header

        for write_call_args in write_calls_args[1:]:  # subsequent calls after writing of header
            write_call_args_list = write_call_args[0][0].split(";")
            pdb_id = write_call_args_list[0]
            assert pdb_id in all_pdb_ids
            assert len(write_call_args_list) == len(CRUNCHED_CSV_FACTOR_ORDER)


def test_crunched_data_csv_raises_on_invalid_path_and_logs(caplog):
    # arrange
    dummy_protein_data_dicts = []
    dummy_path = "dummy path"
    expected_csv_part_in_logs = ";".join(CRUNCHED_CSV_FACTOR_ORDER)

    # act
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(IrrecoverableError):
            create_crunched_csv_file(dummy_protein_data_dicts, dummy_path)

    # assert
    assert len([r for r in caplog.records if r.levelname == "ERROR"]) == 1
    assert len([r for r in caplog.records if r.levelname == "INFO"]) == 1
    assert expected_csv_part_in_logs in caplog.text  # assert the csv got printed into logs
