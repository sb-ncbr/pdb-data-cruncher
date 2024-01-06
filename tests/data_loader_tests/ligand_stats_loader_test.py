from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.models import LigandInfo


def test_ligands_load_correctly(mocker):
    mock_csv = ("LigandID;heavyAtomSize;flexibility\n"
                "000;5;0.125\n"
                "004;11;0.1")

    mocked_csv_open = mocker.mock_open(read_data=mock_csv)
    mocker.patch("builtins.open", mocked_csv_open)

    # act
    ligands = parse_ligand_stats("dummy_path_value")

    # assert
    assert len(ligands) == 2
    assert "000" in ligands.keys() and "004" in ligands.keys()
    assert LigandInfo(5, 0.125) == ligands["000"]
    assert LigandInfo(11, 0.1) == ligands["004"]


def test_ligands_load_skips_invalid_lines(mocker, caplog):
    mock_csv = ("invalid first line\n"
                "000;invalid value;0.125\n"
                "004;11;0.1")

    mocked_csv_open = mocker.mock_open(read_data=mock_csv)
    mocker.patch("builtins.open", mocked_csv_open)

    # act
    ligands = parse_ligand_stats("dummy_path_value")

    # assert
    assert len(ligands) == 1
    assert "000" not in ligands.keys()
    assert "004" in ligands.keys()
    assert LigandInfo(11, 0.1) == ligands["004"]
    # check there were logged exactly two WARNINGs (one for first line, one for skipped ligand line)
    assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 2
