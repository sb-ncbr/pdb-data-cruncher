import os

import pytest

from src.data_parsers.xml_parser import _parse_xml_unsafe
from src.models import ProteinDataFromXML
from tests.test_constants import BASIC_TEST_PDB_IDS, EXTENDED_TEST_PDB_IDS, TEST_DATA_PATH
from tests.helpers import load_data_from_crunched_results_csv, compare_dataclasses, float_or_none


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_xml_basic(pdb_id: str):
    unified_test_parse_xml(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_xml_extended(pdb_id: str):
    unified_test_parse_xml(pdb_id)


def unified_test_parse_xml(pdb_id: str):
    xml_file_path = os.path.join(TEST_DATA_PATH, pdb_id, f"{pdb_id}_validation.xml")

    if not os.path.exists(xml_file_path):
        raise RuntimeError(f"XML file for pdb_id {pdb_id} not found. If that id is part of extended test suite, "
                           "you need to acquire the additional tests data as described in readme, or switch to "
                           "basic test suite only.")

    expected_protein_data = load_expected_xml_protein_data(pdb_id)
    actual_protein_data = _parse_xml_unsafe(pdb_id, xml_file_path)

    assert actual_protein_data

    differences = compare_dataclasses(actual_protein_data, expected_protein_data)
    differences_messages = " ".join([f"{diff[0]}: expected {diff[1]}, got {diff[2]}" for diff in differences])

    assert not differences, differences_messages


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
        highest_chain_bonds_RMSZ=float_or_none(data["highestChainBondsRMSZ"]),
        highest_chain_angles_RMSZ=float_or_none(data["highestChainAnglesRMSZ"]),
        average_residue_RSR=float_or_none(data["averageResidueRSR"]),
        average_residue_RSCC=float_or_none(data["averageResidueRSCC"]),
        residue_RSCC_outlier_ratio=float_or_none(data["residueRSCCoutlierRatio"]),
        average_ligand_RSR=float_or_none(data["averageLigandRSR"]),
        average_ligand_RSCC=float_or_none(data["averageLigandRSCC"]),
        ligand_RSCC_outlier_ratio=float_or_none(data["ligandRSCCoutlierRatio"]),
        average_ligand_angle_RMSZ=float_or_none(data["averageLigandAngleRMSZ"]),
        average_ligand_bond_RMSZ=float_or_none(data["averageLigandBondRMSZ"]),
        average_ligand_RSCC_large_ligands=float_or_none(data["averageLigandRSCCsmallLigs"]),
        average_ligand_RSCC_small_ligands=float_or_none(data["averageLigandRSCClargeLigs"]),
    )
