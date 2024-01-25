import os

import pytest

from src.models import ProteinDataFromPDBx
from src.data_parsers.pdbx_parser import parse_pdbx
from tests.helpers import load_data_from_crunched_results_csv, compare_dataclasses, int_or_none, float_or_none
from tests.test_constants import BASIC_TEST_PDB_IDS, EXTENDED_TEST_PDB_IDS, TEST_DATA_PATH


@pytest.mark.basic
@pytest.mark.parametrize("pdb_id", BASIC_TEST_PDB_IDS)
def test_parse_pdbx_basic(pdb_id: str):
    unified_test_parse_pdbx(pdb_id)


@pytest.mark.extended
@pytest.mark.parametrize("pdb_id", EXTENDED_TEST_PDB_IDS)
def test_parse_pdbx_extended(pdb_id: str):
    unified_test_parse_pdbx(pdb_id)


def unified_test_parse_pdbx(pdb_id: str):
    # arrange
    path_to_pdbx_file = os.path.join(TEST_DATA_PATH, pdb_id, f"{pdb_id}.cif")
    assert os.path.exists(path_to_pdbx_file)
    expected_protein_data = load_expected_pdbx_protein_data(pdb_id)

    # act
    actual_protein_data = parse_pdbx(pdb_id, path_to_pdbx_file)

    # assert
    assert actual_protein_data
    differences = compare_dataclasses(
        actual_protein_data,
        expected_protein_data,
        # TODO these may not be used at all, check after all data collection
        ignored_fields=[
            "struct_keywords_text",
            "struct_keywords_pdbx",
            "refinement_resolution_high",
            "reflections_resolution_high",
            "experimental_method",
            "citation_journal_abbreviation",
            "crystal_grow_methods",
            "crystal_grow_temperatures",
            "crystal_grow_ph",
            "diffraction_ambient_temperature",
            "software_name",
            "gene_source_scientific_name",
            "host_organism_scientific_name",
            "em_3d_reconstruction_resolution",
        ],  # these do not directly influence crunched_results
    )
    assert not differences.count, differences.get_difference_description()


def load_expected_pdbx_protein_data(pdb_id: str):
    data = load_data_from_crunched_results_csv(
        pdb_id,
        [
            "atomCount",
            "aaCount",
            "allAtomCount",
            "allAtomCountLn",
            "hetatmCount",
            "hetatmCountNowater",
            "hetatmCountMetal",
            "hetatmCountNometal",
            "hetatmCountNowaterNometal",
            "ligandCount",
            "ligandCountNowater",
            "ligandCountMetal",
            "ligandCountNometal",
            "ligandCountNowaterNometal",
            "ligandRatio",
            "ligandRatioNowater",
            "ligandRatioMetal",
            "ligandRatioNometal",
            "ligandRatioNowaterNometal",
            "StructureWeight",
            "PolymerWeight",
            "NonpolymerWeightNowater",
            "WaterWeight",
            "NonpolymerWeight",
        ],
    )
    return ProteinDataFromPDBx(
        pdb_id=pdb_id,
        atom_count_without_hetatms=int_or_none(data["atomCount"]),
        aa_count=int_or_none(data["aaCount"]),
        all_atom_count=int_or_none(data["allAtomCount"]),
        all_atom_count_ln=float_or_none(data["allAtomCountLn"]),
        hetatm_count=int_or_none(data["hetatmCount"]),
        hetatm_count_no_water=int_or_none(data["hetatmCountNowater"]),
        hetatm_count_metal=int_or_none(data["hetatmCountMetal"]),
        hetatm_count_no_metal=int_or_none(data["hetatmCountNometal"]),
        hetatm_count_no_water_no_metal=int_or_none(data["hetatmCountNowaterNometal"]),
        ligand_count=int_or_none(data["ligandCount"]),
        ligand_count_no_water=int_or_none(data["ligandCountNowater"]),
        ligand_count_metal=int_or_none(data["ligandCountMetal"]),
        ligand_count_no_metal=int_or_none(data["ligandCountNometal"]),
        ligand_count_no_water_no_metal=int_or_none(data["ligandCountNowaterNometal"]),
        ligand_ratio=float_or_none(data["ligandRatio"]),
        ligand_ratio_no_water=float_or_none(data["ligandRatioNowater"]),
        ligand_ratio_metal=float_or_none(data["ligandRatioMetal"]),
        ligand_ratio_no_metal=float_or_none(data["ligandRatioNometal"]),
        ligand_ratio_no_water_no_metal=float_or_none(data["ligandRatioNowaterNometal"]),
        structure_weight=float_or_none(data["StructureWeight"]),
        polymer_weight=float_or_none(data["PolymerWeight"]),
        nonpolymer_weight_no_water=float_or_none(data["NonpolymerWeightNowater"]),
        water_weight=float_or_none(data["WaterWeight"]),
        nonpolymer_weight=float_or_none(data["NonpolymerWeight"]),
    )
