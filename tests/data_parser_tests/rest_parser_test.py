import os

import pytest

from src.data_loaders.json_file_loader import load_json_file
from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.data_parsers.rest_parser import parse_rest
from src.models import ProteinDataFromRest
from tests.helpers import compare_dataclasses
from tests.helpers import int_or_none, float_or_none, load_data_from_crunched_results_csv
from tests.test_constants import BASIC_TEST_PDB_IDS, EXTENDED_TEST_PDB_IDS, TEST_DATA_PATH


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_rest_basic(pdb_id: str):
    unified_test_parse_rest(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_rest_extended(pdb_id: str):
    unified_test_parse_rest(pdb_id)


def unified_test_parse_rest(pdb_id: str):
    # arrange
    path_to_ligand_stats = os.path.join(TEST_DATA_PATH, "ligandStats.csv")
    path_to_summary_json = os.path.join(TEST_DATA_PATH, pdb_id, "summary", f"{pdb_id}.json")
    path_to_assembly_json = os.path.join(TEST_DATA_PATH, pdb_id, "assembly", f"{pdb_id}.json")
    path_to_molecules_json = os.path.join(TEST_DATA_PATH, pdb_id, "molecules", f"{pdb_id}.json")
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
        molecular_weight=float_or_none(data["AssemblyTotalWeight"]),
        assembly_biopolymer_count=int_or_none(data["AssemblyBiopolymerCount"]),
        assembly_ligand_count=int_or_none(data["AssemblyLigandCount"]),
        assembly_water_count=int_or_none(data["AssemblyWaterCount"]),
        assembly_unique_biopolymer_count=int_or_none(data["AssemblyUniqueBiopolymerCount"]),
        assembly_unique_ligand_count=int_or_none(data["AssemblyUniqueLigandCount"]),
        assembly_biopolymer_weight_kda=float_or_none(data["AssemblyBiopolymerWeight"]),
        assembly_ligand_weight_da=float_or_none(data["AssemblyLigandWeight"]),
        assembly_water_weight_da=float_or_none(data["AssemblyWaterWeight"]),
        assembly_ligand_flexibility=float_or_none(data["AssemblyLigandFlexibility"]),
    )