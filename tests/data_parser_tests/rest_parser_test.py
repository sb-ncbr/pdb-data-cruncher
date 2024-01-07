import pytest

from src.models import ProteinDataFromRest
from src.manager import Manager
from src.config import Config
from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from tests.helpers import compare_dataclasses


protein_data_8jip = ProteinDataFromRest(
    pdb_id="8jip",
    release_date="2023",
    experimental_method_class="em",
    submission_site="PDBJ",
    processing_site="PDBC",
    molecular_weight=157.421,
    assembly_biopolymer_count=6,
    assembly_ligand_count=1,
    assembly_water_count=0,
    assembly_unique_biopolymer_count=6,
    assembly_unique_ligand_count=1,
    assembly_biopolymer_weight=157.035,
    assembly_ligand_weight=385.538,
    assembly_water_weight=0,
    assembly_ligand_flexibility=0.307692,
)


expected_protein_data_sets = {
    "8jip": protein_data_8jip
}


@pytest.mark.parametrize("pdb_id", ["8jip"])
def test_parse_rest(pdb_id):
    config = Config(path_to_rest_jsons="./tests/test_data/")
    ligand_stats = parse_ligand_stats("./tests/test_data/ligandStats.csv")
    protein_data = Manager.load_and_parse_json(pdb_id, ligand_stats, config)
    expected_protein_data = expected_protein_data_sets[pdb_id]

    differences = compare_dataclasses(protein_data, expected_protein_data)
    differences_messages = " ".join([f"{diff[0]}: expected {diff[2]}, got {diff[1]}" for diff in differences])

    assert not differences, differences_messages
