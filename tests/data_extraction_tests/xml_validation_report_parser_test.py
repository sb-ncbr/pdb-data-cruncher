import pytest

from src.data_extraction.ligand_stats_parser import parse_ligand_stats
from src.data_extraction.xml_validation_report_parser import parse_xml_validation_report
from tests.test_constants import *
from tests.utils import compare_dataclasses
from tests.expected_results_loader import load_expected_xml_protein_data

PDB_IDS_WITHOUT_XML_VALIDATION_REPORT = []


@pytest.mark.parametrize("pdb_id", TEST_PDB_IDS)
def test_parse_xml_validation_report_basic(pdb_id: str):
    if pdb_id in PDB_IDS_WITHOUT_XML_VALIDATION_REPORT:
        # for some proteins, there is no xml validation file and that is valid
        assert_correct_parse_xml_without_validation_report(pdb_id)
    else:
        assert_correct_parse_xml_with_validation_report(pdb_id)


def assert_correct_parse_xml_without_validation_report(pdb_id: str):
    # arrange
    nonexistent_xml_file_path = path.join(TEST_DATA_PATH, pdb_id, f"{pdb_id}_validation.xml")
    path_to_ligand_stats = path.join(TEST_DATA_PATH, "ligandStats.csv")

    # act
    ligand_stats = parse_ligand_stats(path_to_ligand_stats)
    actual_protein_data = parse_xml_validation_report(pdb_id, nonexistent_xml_file_path, ligand_stats)

    # assert
    assert not actual_protein_data


def assert_correct_parse_xml_with_validation_report(pdb_id: str):
    # arrange
    xml_file_path = path.join(TEST_DATA_PATH, pdb_id, f"{pdb_id}_validation.xml")
    path_to_ligand_stats = path.join(TEST_DATA_PATH, "ligandStats.csv")

    assert path.exists(xml_file_path)
    expected_protein_data = load_expected_xml_protein_data(pdb_id)

    # act
    ligand_stats = parse_ligand_stats(path_to_ligand_stats)
    actual_protein_data = parse_xml_validation_report(pdb_id, xml_file_path, ligand_stats)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(actual_protein_data, expected_protein_data)
    assert not differences.count, differences.get_difference_description()
