import os

import pytest

from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.data_parsers.xml_validation_report_parser import parse_xml_validation_report
from src.models import ProteinDataFromXML
from tests.test_constants import BASIC_TEST_PDB_IDS, EXTENDED_TEST_PDB_IDS, TEST_DATA_PATH
from tests.helpers import load_data_from_crunched_results_csv, compare_dataclasses, float_or_none


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_xml_validation_report_basic(pdb_id: str):
    unified_test_parse_xml_validation_report(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_xml_validation_report_extended(pdb_id: str):
    unified_test_parse_xml_validation_report(pdb_id)


def unified_test_parse_xml_validation_report(pdb_id: str):
    # arrange
    path_to_ligand_stats = os.path.join(TEST_DATA_PATH, "ligandStats.csv")
    xml_file_path = os.path.join(TEST_DATA_PATH, pdb_id, f"{pdb_id}_validation.xml")
    assert os.path.exists(xml_file_path)
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
        highest_chain_bonds_rmsz=float_or_none(data["highestChainBondsRMSZ"]),
        highest_chain_angles_rmsz=float_or_none(data["highestChainAnglesRMSZ"]),
        average_residue_rsr=float_or_none(data["averageResidueRSR"]),
        average_residue_rscc=float_or_none(data["averageResidueRSCC"]),
        residue_rscc_outlier_ratio=float_or_none(data["residueRSCCoutlierRatio"]),
        average_ligand_rsr=float_or_none(data["averageLigandRSR"]),
        average_ligand_rscc=float_or_none(data["averageLigandRSCC"]),
        ligand_rscc_outlier_ratio=float_or_none(data["ligandRSCCoutlierRatio"]),
        average_ligand_angle_rmsz=float_or_none(data["averageLigandAngleRMSZ"]),
        average_ligand_bond_rmsz=float_or_none(data["averageLigandBondRMSZ"]),
        average_ligand_rscc_large_ligands=float_or_none(data["averageLigandRSCClargeLigs"]),
        average_ligand_rscc_small_ligands=float_or_none(data["averageLigandRSCCsmallLigs"]),
    )
