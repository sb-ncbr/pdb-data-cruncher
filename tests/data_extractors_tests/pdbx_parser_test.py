import pytest

from src.data_extraction.pdbx_parser import parse_pdbx
from tests.utils import compare_dataclasses
from tests.expected_results_loader import load_expected_pdbx_protein_data
from tests.test_constants import *


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_pdbx_basic(pdb_id: str):
    unified_test_parse_pdbx(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_pdbx_extended(pdb_id: str):
    unified_test_parse_pdbx(pdb_id, True)


def unified_test_parse_pdbx(pdb_id: str, extended: bool = False):
    # arrange
    test_data_root_path = EXTENDED_TEST_DATA_PATH if extended else BASIC_TEST_DATA_PATH
    path_to_pdbx_file = path.join(test_data_root_path, pdb_id, f"{pdb_id}.cif")
    assert path.exists(path_to_pdbx_file)
    expected_protein_data = load_expected_pdbx_protein_data(pdb_id)

    # act
    actual_protein_data = parse_pdbx(pdb_id, path_to_pdbx_file)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(
        actual_protein_data,
        expected_protein_data,
        # TODO these may not be used at all, check after all data collection
        ignored_fields=[
            "struct_keywords_text",
            "struct_keywords_pdbx",
            "experimental_method",
            "citation_journal_abbreviation",
            "crystal_grow_methods",
            "crystal_grow_temperatures",
            "crystal_grow_ph",
            "diffraction_ambient_temperature",
            "software_name",
            "gene_source_scientific_name",
            "host_organism_scientific_name",
        ],  # these do not directly influence crunched_results
    )
    assert not differences.count, differences.get_difference_description()
