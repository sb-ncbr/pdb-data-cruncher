import pytest

from src.data_extraction.pdbx_parser import parse_pdbx
from tests.utils import compare_dataclasses
from tests.expected_results_loader import load_expected_pdbx_protein_data
from tests.test_constants import *


@pytest.mark.parametrize("pdb_id", TEST_PDB_IDS)
def test_parse_pdbx_basic(pdb_id: str):
    # arrange
    path_to_pdbx_file = path.join(TEST_DATA_PATH, pdb_id, f"{pdb_id}.cif")
    assert path.exists(path_to_pdbx_file)
    expected_protein_data = load_expected_pdbx_protein_data(pdb_id)

    # act
    actual_protein_data = parse_pdbx(pdb_id, path_to_pdbx_file)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(
        actual_protein_data,
        expected_protein_data,
    )
    assert not differences.count, differences.get_difference_description()
