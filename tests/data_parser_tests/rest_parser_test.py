import os

import pytest

from src.data_loaders.json_file_loader import load_json_file
from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.data_parsers.rest_parser import parse_rest
from src.models import ProteinDataFromRest
from src.utils import to_float, to_int
from tests.helpers import compare_dataclasses
from tests.helpers import load_data_from_crunched_results_csv
from tests.test_constants import *


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_rest_basic(pdb_id: str):
    unified_test_parse_rest(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_rest_extended(pdb_id: str):
    unified_test_parse_rest(pdb_id, extended=True)


def unified_test_parse_rest(pdb_id: str, extended: bool = False):
    # arrange
    test_file_path_root = EXTENDED_TEST_DATA_PATH if extended else BASIC_TEST_DATA_PATH
    path_to_summary_json = os.path.join(test_file_path_root, pdb_id, "summary", f"{pdb_id}.json")
    path_to_assembly_json = os.path.join(test_file_path_root, pdb_id, "assembly", f"{pdb_id}.json")
    path_to_molecules_json = os.path.join(test_file_path_root, pdb_id, "molecules", f"{pdb_id}.json")
    path_to_ligand_stats = os.path.join(TEST_DATA_PATH, "ligandStats.csv")
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
        ignored_fields=["experimental_method_class", "submission_site", "processing_site"],
    )
    assert not differences.count, differences.get_difference_description()


def load_expected_rest_protein_data(pdb_id: str) -> ProteinDataFromRest:
    data = load_data_from_crunched_results_csv(
        pdb_id,
        [
            "releaseDate",
            "AssemblyTotalWeight",
            "AssemblyBiopolymerCount",
            "AssemblyLigandCount",
            "AssemblyWaterCount",
            "AssemblyUniqueBiopolymerCount",
            "AssemblyUniqueLigandCount",
            "AssemblyBiopolymerWeight",
            "AssemblyLigandWeight",
            "AssemblyWaterWeight",
            "AssemblyLigandFlexibility",
        ],
    )
    return ProteinDataFromRest(
        pdb_id=pdb_id,
        release_date=data["releaseDate"],
        molecular_weight=to_float(data["AssemblyTotalWeight"]),
        assembly_biopolymer_count=to_int(data["AssemblyBiopolymerCount"]),
        assembly_ligand_count=to_int(data["AssemblyLigandCount"]),
        assembly_water_count=to_int(data["AssemblyWaterCount"]),
        assembly_unique_biopolymer_count=to_int(data["AssemblyUniqueBiopolymerCount"]),
        assembly_unique_ligand_count=to_int(data["AssemblyUniqueLigandCount"]),
        assembly_biopolymer_weight_kda=to_float(data["AssemblyBiopolymerWeight"]),
        assembly_ligand_weight_da=to_float(data["AssemblyLigandWeight"]),
        assembly_water_weight_da=to_float(data["AssemblyWaterWeight"]),
        assembly_ligand_flexibility=to_float(data["AssemblyLigandFlexibility"]),
    )
