import pytest

from src.models.protein_data_from_pdbx import ProteinDataFromPDBx
from src.data_parsers.pdbx_parser import _parse_pdbx_unsafe
from tests.helpers import compare_dataclasses


# small testing protein
protein_data_8jip = ProteinDataFromPDBx(
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
    water_weight=0,
    structure_keywords=[
        "G protein-coupled receptor",
        "ligand recognition",
        "receptor activation",
        "unimolecular dual agonist",
        "STRUCTURAL PROTEIN",
    ],
)


# has water molecules
protein_data_1cbs = ProteinDataFromPDBx(
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
    water_weight=1801.5,
    structure_keywords=["RETINOIC-ACID TRANSPORT"],
)


# has some issues in the structure
protein_data_6n6n = ProteinDataFromPDBx(
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
    water_weight=8809.34,
    structure_keywords=["FtsY", "SRP", "Signal recognition particle receptor", "SR", "TRANSPORT PROTEIN"],
)


# larger sample but no hetatm
protein_data_1a5j = ProteinDataFromPDBx(
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
    water_weight=0,
    structure_keywords=["DNA-BINDING PROTEIN", "PROTOONCOGENE PRODUCT", "DNA BINDING PROTEIN"],
)


expected_protein_data_sets = {
    "8jip": protein_data_8jip,
    "1cbs": protein_data_1cbs,
    "6n6n": protein_data_6n6n,
    "1a5j": protein_data_1a5j,
}


@pytest.mark.parametrize("pdb_id", ["8jip", "1cbs", "6n6n", "1a5j"])
def test_pdbx_parser(pdb_id):
    protein_data = _parse_pdbx_unsafe(pdb_id, f"./tests/test_data/{pdb_id}.cif")
    expected_protein_data = expected_protein_data_sets[pdb_id]

    # TODO use this when weights are implemented
    # differences = compare_dataclasses(protein_data, expected_protein_data)
    differences = compare_dataclasses(
        protein_data,
        expected_protein_data,
        [
            "structure_weight",
            "polymer_weight",
            "nonpolymer_weight",
            "nonpolymer_weight_no_water",
            "water_weight",
        ]
    )
    differences_messages = " ".join([f"{diff[0]}: expected {diff[2]}, got {diff[1]}" for diff in differences])

    assert not differences, differences_messages
