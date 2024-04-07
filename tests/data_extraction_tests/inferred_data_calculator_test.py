import pytest

from src.data_extraction.inferred_protein_data_calculator import calculate_inferred_protein_data
from src.models.protein_data import ProteinDataComplete
from tests.test_constants import *
from tests.expected_results_loader import (
    load_expected_inferred_data,
    load_expected_validator_db_protein_data,
    load_expected_pdbx_protein_data,
    load_expected_rest_protein_data,
    load_expected_xml_protein_data,
)
from tests.utils import compare_dataclasses


@pytest.mark.parametrize("pdb_id", TEST_PDB_IDS)
def test_calculate_inferred_protein_data_basic(pdb_id: str):
    # arrange
    pre_loaded_protein_data = ProteinDataComplete(
        pdb_id=pdb_id,
        pdbx=load_expected_pdbx_protein_data(pdb_id),
        rest=load_expected_rest_protein_data(pdb_id),
        vdb=load_expected_validator_db_protein_data(pdb_id),
        xml=load_expected_xml_protein_data(pdb_id),
    )
    expected_inferred_data = load_expected_inferred_data(pdb_id)

    # act
    calculate_inferred_protein_data(pre_loaded_protein_data)
    actual_inferred_data = pre_loaded_protein_data.inferred

    # assert
    assert actual_inferred_data is not None
    differences = compare_dataclasses(
        actual_inferred_data,
        expected_inferred_data,
    )
    assert not differences.count, differences.get_difference_description()
