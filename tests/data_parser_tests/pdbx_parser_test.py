import pytest

from src.models import ProteinDataFromPDBx
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
    struct_keywords_text=[
        "G protein-coupled receptor",
        "ligand recognition",
        "receptor activation",
        "unimolecular dual agonist",
        "STRUCTURAL PROTEIN",
    ],
    em_3d_reconstruction_resolution=2.85,
    experimental_method="ELECTRON MICROSCOPY",
    struct_keywords_pdbx="STRUCTURAL PROTEIN",
    gene_source_scientific_name=["Homo sapiens", "Homo sapiens", "Rattus norvegicus", "Bos taurus", "Escherichia coli"],
    host_organism_scientific_name=[
        "Spodoptera frugiperda",
        "Spodoptera frugiperda",
        "Spodoptera frugiperda",
        "Spodoptera frugiperda",
        "Escherichia coli",
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
    struct_keywords_text=["RETINOIC-ACID TRANSPORT"],
    experimental_method="X-RAY DIFFRACTION",
    software_name=["X-PLOR", "X-PLOR", "X-PLOR"],
    struct_keywords_pdbx="RETINOIC-ACID TRANSPORT",
    refinement_resolution_high=1.8,
    gene_source_scientific_name=["Homo sapiens"],
    host_organism_scientific_name=["Escherichia coli BL21(DE3)"],
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
    struct_keywords_text=["FtsY", "SRP", "Signal recognition particle receptor", "SR", "TRANSPORT PROTEIN"],
    experimental_method="X-RAY DIFFRACTION",
    software_name=["PHENIX", "XDS", "Aimless", "MOLREP"],
    struct_keywords_pdbx="TRANSPORT PROTEIN",
    reflections_resolution_high=1.877,
    refinement_resolution_high=1.877,
    diffraction_ambient_temperature=100,
    gene_source_scientific_name=["Escherichia coli (strain K12)"],
    host_organism_scientific_name=["Escherichia coli 'BL21-Gold(DE3)pLysS AG'"],
    crystal_grow_methods=["VAPOR DIFFUSION", "SITTING DROP"],
    crystal_grow_temperature=297.15,
    crystal_grow_ph=5.8,
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
    struct_keywords_text=["DNA-BINDING PROTEIN", "PROTOONCOGENE PRODUCT", "DNA BINDING PROTEIN"],
    experimental_method="SOLUTION NMR",
    software_name=["DYANA", "DYANA"],
    struct_keywords_pdbx="DNA BINDING PROTEIN",
    gene_source_scientific_name=["Gallus gallus"],
    host_organism_scientific_name=["Escherichia coli"],
)


expected_protein_data_sets = {
    "8jip": protein_data_8jip,
    "1cbs": protein_data_1cbs,
    "6n6n": protein_data_6n6n,
    "1a5j": protein_data_1a5j,
}


@pytest.mark.old
@pytest.mark.parametrize("pdb_id", ["8jip", "1cbs", "6n6n", "1a5j"])
def test_pdbx_parser(pdb_id):
    protein_data, _ = _parse_pdbx_unsafe(pdb_id, f"./tests/test_data_2/{pdb_id}.cif")
    expected_protein_data = expected_protein_data_sets[pdb_id]

    differences = compare_dataclasses(
        protein_data,
        expected_protein_data,
        ignored_fields=[  # ignored fields that are not compared
            "citation_journal_abbreviation",
        ],
        float_precision=1e-1,
    )
    differences_messages = " ".join([f"{diff[0]}: expected {diff[1]}, got {diff[2]}" for diff in differences])

    assert not differences, differences_messages
