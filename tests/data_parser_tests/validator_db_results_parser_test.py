import os

import pytest

from src.data_loaders.json_file_loader import load_json_file
from src.data_parsers.validator_db_result_parser import parse_validator_db_result
from src.models import ProteinDataFromVDB
from src.utils import to_float, to_int
from tests.test_constants import *
from tests.helpers import load_data_from_crunched_results_csv, compare_dataclasses


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
    path_to_result_json = os.path.join(test_data_root, pdb_id, "result.json")
    expected_protein_data = load_expected_validator_db_protein_data(pdb_id)

    # act
    result_json = load_json_file(path_to_result_json)
    actual_protein_data = parse_validator_db_result(pdb_id, result_json)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(
        actual_protein_data,
        expected_protein_data,
        ignored_fields=[
            "missing_precise",
            "missing_carbon_chiral_errors_precise",
            "analyzed",
            "not_analyzed",
            "has_all_bad_chirality_carbon",
            "missing_atoms",
            "missing_rings",
            "ligand_quality_ratios"
        ]
    )
    assert not differences.count, differences.get_difference_description()


def load_expected_validator_db_protein_data(pdb_id: str) -> ProteinDataFromVDB:
    data = load_data_from_crunched_results_csv(
        pdb_id,
        [
            "hetatmCountFiltered",
            "ligandCarbonChiraAtomCountFiltered",
            "ligandCountFiltered",
            "hetatmCountFilteredMetal",
            "ligandCountFilteredMetal",
            "hetatmCountFilteredNometal",
            "ligandCountFilteredNometal",
            "ligandRatioFiltered",
            "ligandRatioFilteredMetal",
            "ligandRatioFilteredNometal",
            "ligandBondRotationFreedom",
            "ChiraProblemsPrecise",
        ]
    )
    return ProteinDataFromVDB(
        pdb_id=pdb_id,
        hetatm_count_filtered=to_int(data["hetatmCountFiltered"]),
        ligand_carbon_chiral_atom_count_filtered=to_int(data["ligandCarbonChiraAtomCountFiltered"]),
        ligand_count_filtered=to_int(data["ligandCountFiltered"]),
        hetatm_count_filtered_metal=to_int(data["hetatmCountFilteredMetal"]),
        ligand_count_filtered_metal=to_int(data["ligandCountFilteredMetal"]),
        hetatm_count_filtered_no_metal=to_int(data["hetatmCountFilteredNometal"]),
        ligand_count_filtered_no_metal=to_int(data["ligandCountFilteredNometal"]),
        ligand_ratio_filtered=to_float(data["ligandRatioFiltered"]),
        ligand_ratio_filtered_metal=to_float(data["ligandRatioFilteredMetal"]),
        ligand_ratio_filtered_no_metal=to_float(data["ligandRatioFilteredNometal"]),
        ligand_bond_rotation_freedom=to_float(data["ligandBondRotationFreedom"]),
        chiral_problems_precise=to_float(data["ChiraProblemsPrecise"])
    )
