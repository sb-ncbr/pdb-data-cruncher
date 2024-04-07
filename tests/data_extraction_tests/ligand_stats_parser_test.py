from os import path

import pytest

from src.data_extraction.ligand_stats_parser import calculate_ligand_stats
from src.models.ids_to_update import IdsToUpdateAndRemove
from src.data_extraction.ligand_stats_parser import parse_ligand_stats
from src.models import LigandInfo
from tests.test_constants import TEST_DATA_PATH, TEST_LIGAND_IDS
from tests.utils import compare_dataclasses


def test_ligands_load_correctly(mocker):
    mock_csv = "LigandID;heavyAtomSize;flexibility\n000;5;0.125\n004;11;0.1"

    mocked_csv_open = mocker.mock_open(read_data=mock_csv)
    mocker.patch("builtins.open", mocked_csv_open)

    # act
    ligands = parse_ligand_stats("dummy_path_value")

    # assert
    assert len(ligands) == 2
    assert "000" in ligands and "004" in ligands
    assert LigandInfo("000", 5, 0.125) == ligands["000"]
    assert LigandInfo("004", 11, 0.1) == ligands["004"]


def test_ligands_load_skips_invalid_lines(mocker, caplog):
    mock_csv = "invalid first line\n000;invalid value;0.125\n004;11;0.1"

    mocked_csv_open = mocker.mock_open(read_data=mock_csv)
    mocker.patch("builtins.open", mocked_csv_open)

    # act
    ligands = parse_ligand_stats("dummy_path_value")

    # assert
    assert len(ligands) == 1
    assert "000" not in ligands
    assert "004" in ligands
    assert LigandInfo("004", 11, 0.1) == ligands["004"]
    # check there were logged exactly two WARNINGs (one for first line, one for skipped ligand line)
    assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 2


EXPECTED_LIGAND_STATS = {
    "AOH": LigandInfo(id="AOH", heavy_atom_count=61, flexibility=0.124031),
    "CBY": LigandInfo(id="CBY", heavy_atom_count=68, flexibility=0.142857),
    "IX3": LigandInfo(id="IX3", heavy_atom_count=13, flexibility=0.0),
    "MN3": LigandInfo(id="MN3", heavy_atom_count=1, flexibility=1.0),
    "OT1": LigandInfo(id="OT1", heavy_atom_count=23, flexibility=0.0185185),
    "QON": LigandInfo(id="QON", heavy_atom_count=21, flexibility=0.146341),
}


@pytest.mark.parametrize("ligand_id", TEST_LIGAND_IDS)
def test_calculate_ligand_stats(ligand_id):
    ligand_cifs_filepath = path.join(TEST_DATA_PATH, "ligand_ccd_CIF")

    ids_to_update_and_remove = IdsToUpdateAndRemove(ligands_to_update=[ligand_id])
    calculated_ligand_stats = calculate_ligand_stats(ligand_cifs_filepath, ids_to_update_and_remove)

    assert calculated_ligand_stats
    assert len(calculated_ligand_stats) == 1

    actual_ligand_stat = calculated_ligand_stats[0]
    expected_ligand_stat = EXPECTED_LIGAND_STATS[ligand_id]

    differences = compare_dataclasses(actual_ligand_stat, expected_ligand_stat)
    assert not differences.count, differences.get_difference_description()
