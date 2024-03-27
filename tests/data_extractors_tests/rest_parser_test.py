import pytest

from src.file_handlers.json_file_loader import load_json_file
from src.data_extraction.ligand_stats_parser import parse_ligand_stats
from src.data_extraction.rest_parser import parse_rest
from tests.utils import compare_dataclasses
from tests.expected_results_loader import load_expected_rest_protein_data
from tests.test_constants import *


@pytest.mark.parametrize("pdb_id", TEST_PDB_IDS)
def test_parse_rest_basic(pdb_id: str):
    # arrange
    path_to_summary_json = path.join(TEST_DATA_PATH, pdb_id, "summary", f"{pdb_id}.json")
    path_to_assembly_json = path.join(TEST_DATA_PATH, pdb_id, "assembly", f"{pdb_id}.json")
    path_to_molecules_json = path.join(TEST_DATA_PATH, pdb_id, "molecules", f"{pdb_id}.json")
    path_to_ligand_stats = path.join(TEST_DATA_PATH, "ligandStats.csv")
    expected_protein_data = load_expected_rest_protein_data(pdb_id)

    # act
    ligand_stats = parse_ligand_stats(path_to_ligand_stats)
    summary_json = load_json_file(path_to_summary_json)
    assembly_json = load_json_file(path_to_assembly_json)
    molecules_json = load_json_file(path_to_molecules_json)
    actual_protein_data = parse_rest(pdb_id, summary_json, assembly_json, molecules_json, ligand_stats)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(
        actual_protein_data,
        expected_protein_data,
    )
    assert not differences.count, differences.get_difference_description()
