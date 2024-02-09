from os import path

import pytest

from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.data_parsers.xml_validation_report_parser import parse_xml_validation_report
from src.models import ProteinDataFromXML
from src.utils import to_float
from tests.test_constants import *
from tests.helpers import load_data_from_crunched_results_csv, compare_dataclasses


PDB_IDS_WITHOUT_XML_VALIDATION_REPORT = ["8ckb"]


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_xml_validation_report_basic(pdb_id: str):
    unified_test_parse_xml_validation_report(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_xml_validation_report_extended(pdb_id: str):
    unified_test_parse_xml_validation_report(pdb_id, True)


def unified_test_parse_xml_validation_report(pdb_id: str, extended: bool = False):
    if pdb_id in PDB_IDS_WITHOUT_XML_VALIDATION_REPORT:
        # for some proteins, there is no xml validation file and that is valid
        assert_correct_parse_xml_without_validation_report(pdb_id, extended)
    else:
        assert_correct_parse_xml_with_validation_report(pdb_id, extended)


def assert_correct_parse_xml_without_validation_report(pdb_id: str, extended: bool = False):
    # arrange
    test_data_root = EXTENDED_TEST_DATA_PATH if extended else BASIC_TEST_DATA_PATH
    nonexistent_xml_file_path = path.join(test_data_root, pdb_id, f"{pdb_id}_validation.xml")
    path_to_ligand_stats = path.join(TEST_DATA_PATH, "ligandStats.csv")

    # act
    ligand_stats = parse_ligand_stats(path_to_ligand_stats)
    actual_protein_data = parse_xml_validation_report(pdb_id, nonexistent_xml_file_path, ligand_stats)

    # assert
    assert not actual_protein_data


def assert_correct_parse_xml_with_validation_report(pdb_id: str, extended: bool = False):
    # arrange
    test_data_root = EXTENDED_TEST_DATA_PATH if extended else BASIC_TEST_DATA_PATH
    xml_file_path = path.join(test_data_root, pdb_id, f"{pdb_id}_validation.xml")
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


def load_expected_xml_protein_data(pdb_id: str) -> ProteinDataFromXML:
    data = load_data_from_crunched_results_csv(
        pdb_id,
        [
            "highestChainBondsRMSZ",
            "highestChainAnglesRMSZ",
            "averageResidueRSR",
            "averageResidueRSCC",
            "residueRSCCoutlierRatio",
            "averageLigandRSR",
            "averageLigandRSCC",
            "ligandRSCCoutlierRatio",
            "averageLigandAngleRMSZ",
            "averageLigandBondRMSZ",
            "averageLigandRSCCsmallLigs",
            "averageLigandRSCClargeLigs",
        ],
    )
    return ProteinDataFromXML(
        pdb_id=pdb_id,
        highest_chain_bonds_rmsz=to_float(data["highestChainBondsRMSZ"]),
        highest_chain_angles_rmsz=to_float(data["highestChainAnglesRMSZ"]),
        average_residue_rsr=to_float(data["averageResidueRSR"]),
        average_residue_rscc=to_float(data["averageResidueRSCC"]),
        residue_rscc_outlier_ratio=to_float(data["residueRSCCoutlierRatio"]),
        average_ligand_rsr=to_float(data["averageLigandRSR"]),
        average_ligand_rscc=to_float(data["averageLigandRSCC"]),
        ligand_rscc_outlier_ratio=to_float(data["ligandRSCCoutlierRatio"]),
        average_ligand_angle_rmsz=to_float(data["averageLigandAngleRMSZ"]),
        average_ligand_bond_rmsz=to_float(data["averageLigandBondRMSZ"]),
        average_ligand_rscc_large_ligands=to_float(data["averageLigandRSCClargeLigs"]),
        average_ligand_rscc_small_ligands=to_float(data["averageLigandRSCCsmallLigs"]),
    )
