import csv

from tests.test_constants import CRUNCHED_RESULTS_CSV_PATH
from src.models import ProteinDataFromXML, ProteinDataFromVDB, ProteinDataFromPDBx, ProteinDataFromRest
from src.utils import to_int, to_float


def load_data_from_crunched_results_csv(pdb_id: str, fields: list[str]) -> dict[str, str]:
    """
    Loads data from crunched_results.csv and returns only relevant field values.
    :param pdb_id: PDB ID of structure data to load.
    :param fields: Fields to exctract.
    :return: Dict where keys are given field names, and values are extracted values (as strings).
    :raises RuntimeError: If PDB ID is not found in csv or one or more fields are not found.
    """
    with open(CRUNCHED_RESULTS_CSV_PATH, encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        first_row = next(csv_reader)
        relevant_row = None
        current_row = next(csv_reader)
        while current_row:
            if current_row[0] == pdb_id:
                relevant_row = current_row
                break
            current_row = next(csv_reader)

        if not relevant_row:
            raise RuntimeError(f"Row with pdb_id {pdb_id} not found in csv file.")

    extracted_fields = {}
    for index, field_name in enumerate(first_row):
        if field_name in fields:
            if relevant_row[index] == "nan":
                extracted_fields[field_name] = None
            else:
                extracted_fields[field_name] = relevant_row[index]

    if len(extracted_fields) != len(fields):
        not_found_fields = [field_name for field_name in fields if field_name not in extracted_fields]
        raise RuntimeError(f"{len(not_found_fields)} fields not found in csv file: {not_found_fields}")

    return extracted_fields


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
        atom_count_without_hetatms=to_int(data["atomCount"]),
        aa_count=to_int(data["aaCount"]),
        all_atom_count=to_int(data["allAtomCount"]),
        all_atom_count_ln=to_float(data["allAtomCountLn"]),
        hetatm_count=to_int(data["hetatmCount"]),
        hetatm_count_no_water=to_int(data["hetatmCountNowater"]),
        hetatm_count_metal=to_int(data["hetatmCountMetal"]),
        hetatm_count_no_metal=to_int(data["hetatmCountNometal"]),
        hetatm_count_no_water_no_metal=to_int(data["hetatmCountNowaterNometal"]),
        ligand_count=to_int(data["ligandCount"]),
        ligand_count_no_water=to_int(data["ligandCountNowater"]),
        ligand_count_metal=to_int(data["ligandCountMetal"]),
        ligand_count_no_metal=to_int(data["ligandCountNometal"]),
        ligand_count_no_water_no_metal=to_int(data["ligandCountNowaterNometal"]),
        ligand_ratio=to_float(data["ligandRatio"]),
        ligand_ratio_no_water=to_float(data["ligandRatioNowater"]),
        ligand_ratio_metal=to_float(data["ligandRatioMetal"]),
        ligand_ratio_no_metal=to_float(data["ligandRatioNometal"]),
        ligand_ratio_no_water_no_metal=to_float(data["ligandRatioNowaterNometal"]),
        structure_weight_kda=to_float(data["StructureWeight"]),
        polymer_weight_kda=to_float(data["PolymerWeight"]),
        nonpolymer_weight_no_water_da=to_float(data["NonpolymerWeightNowater"]),
        water_weight_da=to_float(data["WaterWeight"]),
        nonpolymer_weight_da=to_float(data["NonpolymerWeight"]),
    )


def load_expected_rest_protein_data(pdb_id: str) -> ProteinDataFromRest:
    data = load_data_from_crunched_results_csv(
        pdb_id,
        [
            "releaseDate",
            "AssemblyTotalWeight",
            "AssemblyBiopolymerCount",
            "AssemblyLigandCount",
            "AssemblyWaterCount",
            "AssemblyUniqueBiopolymerCount",
            "AssemblyUniqueLigandCount",
            "AssemblyBiopolymerWeight",
            "AssemblyLigandWeight",
            "AssemblyWaterWeight",
            "AssemblyLigandFlexibility",
        ],
    )
    return ProteinDataFromRest(
        pdb_id=pdb_id,
        release_date=data["releaseDate"],
        molecular_weight=to_float(data["AssemblyTotalWeight"]),
        assembly_biopolymer_count=to_int(data["AssemblyBiopolymerCount"]),
        assembly_ligand_count=to_int(data["AssemblyLigandCount"]),
        assembly_water_count=to_int(data["AssemblyWaterCount"]),
        assembly_unique_biopolymer_count=to_int(data["AssemblyUniqueBiopolymerCount"]),
        assembly_unique_ligand_count=to_int(data["AssemblyUniqueLigandCount"]),
        assembly_biopolymer_weight_kda=to_float(data["AssemblyBiopolymerWeight"]),
        assembly_ligand_weight_da=to_float(data["AssemblyLigandWeight"]),
        assembly_water_weight_da=to_float(data["AssemblyWaterWeight"]),
        assembly_ligand_flexibility=to_float(data["AssemblyLigandFlexibility"]),
    )


def load_expected_validator_db_protein_data(pdb_id: str) -> ProteinDataFromVDB:
    data = load_data_from_crunched_results_csv(
        pdb_id,
        [
            "hetatmCountFiltered",
            "ligandCarbonChiraAtomCountFiltered",
            "ligandCountFiltered",
            "hetatmCountFilteredMetal",
            "ligandCountFilteredMetal",
            "hetatmCountFilteredNometal",
            "ligandCountFilteredNometal",
            "ligandRatioFiltered",
            "ligandRatioFilteredMetal",
            "ligandRatioFilteredNometal",
            "ligandBondRotationFreedom",
            "ChiraProblemsPrecise",
        ]
    )
    return ProteinDataFromVDB(
        pdb_id=pdb_id,
        hetatm_count_filtered=to_int(data["hetatmCountFiltered"]),
        ligand_carbon_chiral_atom_count_filtered=to_int(data["ligandCarbonChiraAtomCountFiltered"]),
        ligand_count_filtered=to_int(data["ligandCountFiltered"]),
        hetatm_count_filtered_metal=to_int(data["hetatmCountFilteredMetal"]),
        ligand_count_filtered_metal=to_int(data["ligandCountFilteredMetal"]),
        hetatm_count_filtered_no_metal=to_int(data["hetatmCountFilteredNometal"]),
        ligand_count_filtered_no_metal=to_int(data["ligandCountFilteredNometal"]),
        ligand_ratio_filtered=to_float(data["ligandRatioFiltered"]),
        ligand_ratio_filtered_metal=to_float(data["ligandRatioFilteredMetal"]),
        ligand_ratio_filtered_no_metal=to_float(data["ligandRatioFilteredNometal"]),
        ligand_bond_rotation_freedom=to_float(data["ligandBondRotationFreedom"]),
        chiral_problems_precise=to_float(data["ChiraProblemsPrecise"])
    )


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
