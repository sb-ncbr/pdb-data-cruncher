import pytest
import dataclasses

from src.models.protein_data_from_pdb import ProteinDataFromPDB
from src.data_parsers.pdbx_parser import _parse_pdbx_unsafe, _parse_pdbx_unsafe_alternative
from src.config import Config


# small testing protein
protein_data_8jip = ProteinDataFromPDB(
    pdb_id="8jip",
    atom_count_without_hetatms=9336,
    aa_count=1385,
    all_atom_count=9399,
    all_atom_count_ln=9.14836,
    hetatm_count=63,
    hetatm_count_no_water=63,
    hetatm_count_metal=0,
    hetatm_count_no_metal=63,
    hetatm_count_no_water_no_metal=63,
    ligand_count=1,
    ligand_count_no_water=1,
    ligand_count_metal=0,
    ligand_count_no_metal=1,
    ligand_count_no_water_no_metal=1,
    ligand_ratio=63,
    ligand_ratio_no_water=63,
    ligand_ratio_metal=None,
    ligand_ratio_no_metal=63,
    ligand_ratio_no_water_no_metal=63,
    structure_weight=157.421,
    polymer_weight=157.035,
    nonpolymer_weight=385.538,
    nonpolymer_weight_no_water=385.538,
    water_weight=0
)


# has water molecules
protein_data_1cbs = ProteinDataFromPDB(
    pdb_id="1cbs",
    atom_count_without_hetatms=1091,
    aa_count=137,
    all_atom_count=1213,
    all_atom_count_ln=7.10085,
    hetatm_count=122,
    hetatm_count_no_water=22,
    hetatm_count_metal=0,
    hetatm_count_no_metal=122,
    hetatm_count_no_water_no_metal=22,
    ligand_count=101,
    ligand_count_no_water=1,
    ligand_count_metal=0,
    ligand_count_no_metal=101,
    ligand_count_no_water_no_metal=1,
    ligand_ratio=1.20792,
    ligand_ratio_no_water=22,
    ligand_ratio_metal=None,
    ligand_ratio_no_metal=1.20792,
    ligand_ratio_no_water_no_metal=22,
    structure_weight=17.6837,
    polymer_weight=15.5818,
    nonpolymer_weight=2101.93,
    nonpolymer_weight_no_water=300.435,
    water_weight=1801.5
)


# has some issues in the structure
protein_data_6n6n = ProteinDataFromPDB(
    pdb_id="6n6n",
    atom_count_without_hetatms=9514,
    aa_count=303,
    all_atom_count=10121,
    all_atom_count_ln=9.22237,
    hetatm_count=607,
    hetatm_count_no_water=118,
    hetatm_count_metal=5,
    hetatm_count_no_metal=602,
    hetatm_count_no_water_no_metal=113,
    ligand_count=498,
    ligand_count_no_water=9,
    ligand_count_metal=5,
    ligand_count_no_metal=493,
    ligand_count_no_water_no_metal=4,
    ligand_ratio=1.21888,
    ligand_ratio_no_water=13.1111,
    ligand_ratio_metal=1,
    ligand_ratio_no_metal=1.2211,
    ligand_ratio_no_water_no_metal=28.25,
    structure_weight=76.3265,
    polymer_weight=66.2021,
    nonpolymer_weight=10124.4,
    nonpolymer_weight_no_water=1315.08,
    water_weight=8809.34
)
# TODO this one does not produce correct atom count wihtout hetatm - could be related to
# structure build warnings
# (only with mmcifparser, with mmcif2dict it works)


# larger sample but no hetatm
protein_data_1a5j = ProteinDataFromPDB(
    pdb_id="1a5j",
    atom_count_without_hetatms=59136,
    aa_count=110,
    all_atom_count=59136,
    all_atom_count_ln=10.9876,
    hetatm_count=0,
    hetatm_count_no_water=0,
    hetatm_count_metal=0,
    hetatm_count_no_metal=0,
    hetatm_count_no_water_no_metal=0,
    ligand_count=0,
    ligand_count_no_water=0,
    ligand_count_metal=0,
    ligand_count_no_metal=0,
    ligand_count_no_water_no_metal=0,
    ligand_ratio=None,
    ligand_ratio_no_water=None,
    ligand_ratio_metal=None,
    ligand_ratio_no_metal=None,
    ligand_ratio_no_water_no_metal=None,
    structure_weight=12.9589,
    polymer_weight=12.9589,
    nonpolymer_weight=0,
    nonpolymer_weight_no_water=0,
    water_weight=0
)


expected_protein_data_sets = {
    "8jip": protein_data_8jip,
    "1cbs": protein_data_1cbs,
    "6n6n": protein_data_6n6n,
    "1a5j": protein_data_1a5j,
}


@pytest.mark.parametrize("pdb_id", [
    "8jip",
    "1cbs",
    "6n6n",
    "1a5j"
])
def test_pdbx_parser(pdb_id):
    protein_data = _parse_pdbx_unsafe_alternative(pdb_id, f"./tests/test_data/{pdb_id}.cif")
    expected_protein_data = expected_protein_data_sets[pdb_id]

    differences = assert_protein_data_equal(protein_data, expected_protein_data)
    differences_messages = " ".join([f"{diff[0]}: expected {diff[2]}, got {diff[1]}" for diff in differences])

    assert not differences, differences_messages


@pytest.mark.parametrize("pdb_id", [
    "8jip",
    "1cbs",
    "6n6n",
    "1a5j"
])
def test_pdbx_parser_non_alt(pdb_id):
    protein_data = _parse_pdbx_unsafe(pdb_id, f"./tests/test_data/{pdb_id}.cif")
    expected_protein_data = expected_protein_data_sets[pdb_id]

    differences = assert_protein_data_equal(protein_data, expected_protein_data)
    differences_messages = " ".join([f"{diff[0]}: expected {diff[2]}, got {diff[1]}" for diff in differences])

    assert not differences, differences_messages


def assert_protein_data_equal(actual: ProteinDataFromPDB, expected: ProteinDataFromPDB):
    differences = []

    for field_name, actual_value in dataclasses.asdict(actual).items():
        expected_value = getattr(expected, field_name)
        if field_name in [
            # "aa_count",
            "structure_weight",
            "polymer_weight", "nonpolymer_weight", "nonpolymer_weight_no_water", "water_weight"
        ]:  # TODO remove this workaround when implemented
            continue
        if type(actual_value) is float:
            if expected_value != pytest.approx(actual_value, abs=1e-3):
                differences.append((field_name, actual_value, expected_value))
        else:
            if actual_value != expected_value:
                differences.append((field_name, actual_value, expected_value))

    return differences
