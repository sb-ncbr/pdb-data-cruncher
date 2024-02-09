import logging
from typing import Any, Optional
from dataclasses import dataclass, field

from src.models import ProteinDataFromVDB, Diagnostics
from src.constants import METAL_ELEMENT_NAMES
from src.utils import to_int


@dataclass(slots=True)
class SummaryCounts:
    """
    Counts extracted from Summary part of result json.
    """

    analyzed: int = 0
    not_analyzed: int = 0
    has_all_bad_chirality_c: int = 0
    missing_atoms: int = 0
    missing_rings: int = 0


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class RawDataFromVDB:
    """
    Data extracted from result.json, before processing into data we need.
    """

    atom_count: int = 0
    carbon_chiral_count: int = 0
    atom_count_in_metal_ligands: int = 0
    missing_atoms: int = 0
    wrong_carbon_chiral_count: int = 0
    motive_count: int = 0
    motive_count_in_metal_ligands: int = 0
    bond_count: int = 0
    sigma_bond_count: int = 0
    has_summaries: bool = False
    summary_counts: SummaryCounts = field(default_factory=SummaryCounts)


def parse_validator_db_result(pdb_id: str, result_json: dict[str, Any]) -> Optional[ProteinDataFromVDB]:
    """
    Extracts and calculates prtein information from given result from Validator DB.
    :param pdb_id: Id of the protein.
    :param result_json: Full content of result.json that is result of Validator DB.
    :return: Extracted ProteinDataFromVDB on success, None on critical failure.
    """
    logging.debug("[%s] Validator DB result parsing started", pdb_id)
    try:
        protein_data, diagnostics = _parse_validator_db_result(pdb_id, result_json)
        diagnostics.process_into_logging("VDB parser", pdb_id)
        return protein_data
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # Want to catch any exception to not kill the whole data processing.
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return None


def _parse_validator_db_result(pdb_id: str, result_json: dict[str, Any]) -> (ProteinDataFromVDB, Diagnostics):
    """
    Extracts and calculates protein information from given result from Validator DB.
    :param pdb_id: Id of the protein.
    :param result_json: Full content of result.json.
    :return: Extracted protein data and diagnostics about non-critical data issues.
    :raises
    """
    protein_data = ProteinDataFromVDB(pdb_id=pdb_id)
    diagnostics = Diagnostics()
    raw_data = _extract_raw_data(result_json, diagnostics)
    _process_raw_data(raw_data, protein_data)
    return protein_data, diagnostics


def _extract_raw_data(result_json: dict[str, Any], diagnostics: Diagnostics) -> RawDataFromVDB:
    raw_data = RawDataFromVDB()
    motive_count = to_int(result_json.get("MotiveCount"))
    if motive_count is None:
        diagnostics.add("Failed to extract value from 'MotiveCount'. Assumed the value as 0.")
    else:
        raw_data.motive_count = motive_count

    for model_json in result_json.get("Models", []):
        model_name = model_json.get("ModelName", "[unknown model name]")
        raw_data.bond_count += len(model_json.get("ModelBonds", {}))
        raw_data.sigma_bond_count += len(
            [bond_type for bond_type in model_json.get("ModelBonds", {}).values() if bond_type == 1]
        )

        summary_json = model_json.get("Summary")
        if not summary_json:
            diagnostics.add(f"Model {model_name} has no summary.")
        else:
            raw_data.has_summaries = True
            _extract_raw_data_from_model_summary(summary_json, model_name, raw_data, diagnostics)

        entry_jsons = model_json.get("Entries")
        if not entry_jsons:
            diagnostics.add(f"Model {model_name} has no entries.")
        else:
            _extract_raw_data_from_model_entries(entry_jsons, model_json, raw_data)
    return raw_data


def _extract_raw_data_from_model_entries(
    entry_jsons: list[dict[str, Any]], model_json: dict[str, Any], raw_data: RawDataFromVDB
) -> None:
    """
    Extracts data from Entry parts of json.
    :param entry_jsons: Jsons representing entries inside model.
    :param model_json: Json representing one model.
    :param raw_data: Extracted data.
    """
    model_atom_count = len(model_json.get("ModelAtomTypes", {}))
    model_carbon_chiral_atom_count = len(model_json.get("ChiralAtomsInfo", {}).get("Carbon", []))
    raw_data.atom_count += len(entry_jsons) * model_atom_count
    raw_data.carbon_chiral_count += len(entry_jsons) * model_carbon_chiral_atom_count

    if _contains_metal(model_json):
        raw_data.atom_count_in_metal_ligands += len(entry_jsons) * model_atom_count
        raw_data.motive_count_in_metal_ligands += len(entry_jsons)

    for entry_json in entry_jsons:
        raw_data.missing_atoms += len(entry_json.get("MissingAtoms", []))
        for chirality_problem in entry_json.get("ChiralityMismatches", {}).values():
            chirality_problem_split = [item for item in chirality_problem.split(" ") if item]  # skips empty parts
            if len(chirality_problem_split) > 1 and chirality_problem_split[1] == "C":
                raw_data.wrong_carbon_chiral_count += 1


def _contains_metal(model_json: dict[str, Any]) -> bool:
    """
    Check if any symbol in model's atom types is a metal.
    :param model_json: Json representing the one model.
    :return: True if at least one of the model's atom types is a metal, false if not.
    """
    model_atom_types = model_json.get("ModelAtomTypes", {})
    for atom_symbol in model_atom_types.values():
        if atom_symbol.lower() in METAL_ELEMENT_NAMES:
            return True
    return False


def _extract_raw_data_from_model_summary(
    summary_json: dict[str, Any], model_name: str, raw_data: RawDataFromVDB, diagnostics: Diagnostics
) -> None:
    """
    Get relevant data from the "Summary" part of one model.
    :param summary_json: Json holding information about the summary.
    :param model_name: Name of the model holding the summary.
    :param raw_data: Where the data is extracted to.
    :param diagnostics: Holding information about data issues.
    """
    analyzed = to_int(summary_json.get("Analyzed"))
    if analyzed is not None:
        raw_data.summary_counts.analyzed += analyzed
    else:
        diagnostics.add(f"Model {model_name} has invalid 'Analyzed' field.")

    not_analyzed = to_int(summary_json.get("NotAnalyzed"))
    if not_analyzed is not None:
        raw_data.summary_counts.not_analyzed += not_analyzed
    else:
        diagnostics.add(f"Model {model_name} has invalid 'NotAnalyzed' field.")

    has_all_bad_chirality_carbon = to_int(summary_json.get("HasAll_BadChirality_Carbon"))
    if has_all_bad_chirality_carbon is not None:
        raw_data.summary_counts.has_all_bad_chirality_c += has_all_bad_chirality_carbon
    else:
        diagnostics.add(f"Model {model_name} has invalid 'HasAll_BadChirality_Carbon' field.")

    missing_atoms = to_int(summary_json.get("Missing_Atoms"))
    if missing_atoms is not None:
        raw_data.summary_counts.missing_atoms += missing_atoms
    else:
        diagnostics.add(f"Model {model_name} has invalid 'Missing_Atoms' field.")

    missing_rings = to_int(summary_json.get("Missing_Rings"))
    if missing_rings is not None:
        raw_data.summary_counts.analyzed += missing_rings
    else:
        diagnostics.add(f"Model {model_name} has invalid 'Missing_Rings' field.")


def _process_raw_data(raw_data: RawDataFromVDB, protein_data: ProteinDataFromVDB) -> None:
    # straightforward items
    protein_data.hetatm_count_filtered = raw_data.atom_count
    protein_data.ligand_carbon_chiral_atom_count_filtered = raw_data.carbon_chiral_count
    protein_data.ligand_count_filtered = raw_data.motive_count
    protein_data.hetatm_count_filtered_metal = raw_data.atom_count_in_metal_ligands
    protein_data.ligand_count_filtered_metal = raw_data.motive_count_in_metal_ligands
    atom_count_without_metal_ligands = raw_data.atom_count - raw_data.atom_count_in_metal_ligands
    motive_count_without_metal_ligands = raw_data.motive_count - raw_data.motive_count_in_metal_ligands
    protein_data.hetatm_count_filtered_no_metal = atom_count_without_metal_ligands
    protein_data.ligand_count_filtered_no_metal = motive_count_without_metal_ligands

    # ratios
    if raw_data.motive_count > 0:
        protein_data.ligand_ratio_filtered = raw_data.atom_count / raw_data.motive_count
    if raw_data.motive_count_in_metal_ligands > 0:
        protein_data.ligand_ratio_filtered_metal = (
            raw_data.atom_count_in_metal_ligands / raw_data.motive_count_in_metal_ligands
        )
    if motive_count_without_metal_ligands > 0:
        protein_data.ligand_ratio_filtered_no_metal = (
            atom_count_without_metal_ligands / motive_count_without_metal_ligands
        )
    if raw_data.bond_count > 0:
        protein_data.ligand_bond_rotation_freedom = raw_data.sigma_bond_count / raw_data.bond_count

    # summaries data
    if raw_data.has_summaries:
        _process_raw_data_from_summaries(raw_data, protein_data)
        if raw_data.motive_count > 0:
            _calculate_ligand_quality_ratios_from_summaries(raw_data, protein_data)


def _process_raw_data_from_summaries(raw_data: RawDataFromVDB, protein_data: ProteinDataFromVDB) -> None:
    missing_atom_ratio = 0
    if raw_data.atom_count > 0:
        missing_atom_ratio = raw_data.summary_counts.missing_atoms / raw_data.atom_count
        protein_data.missing_precise = missing_atom_ratio

    if raw_data.carbon_chiral_count > 0:
        carbon_chiral_problems_ratio = raw_data.wrong_carbon_chiral_count / raw_data.carbon_chiral_count
        protein_data.chiral_problems_precise = carbon_chiral_problems_ratio
        both_problems_ratio = carbon_chiral_problems_ratio + missing_atom_ratio
        protein_data.missing_carbon_chiral_errors_precise = both_problems_ratio
    else:
        protein_data.chiral_problems_precise = 0
        protein_data.missing_carbon_chiral_errors_precise = 0


def _calculate_ligand_quality_ratios_from_summaries(raw_data: RawDataFromVDB, protein_data: ProteinDataFromVDB) -> None:
    missing_atoms_and_rings = raw_data.summary_counts.missing_rings + raw_data.summary_counts.missing_atoms
    has_all_good_chirality_ignore_all_except_carbon = (
        raw_data.motive_count - raw_data.summary_counts.has_all_bad_chirality_c - missing_atoms_and_rings
    )

    protein_data.ligand_quality_ratios.analyzed = raw_data.summary_counts.analyzed / raw_data.motive_count
    protein_data.ligand_quality_ratios.not_analyzed = raw_data.summary_counts.not_analyzed / raw_data.motive_count
    protein_data.ligand_quality_ratios.has_all_good_chirality_c_only = (
        has_all_good_chirality_ignore_all_except_carbon / raw_data.motive_count
    )
    protein_data.ligand_quality_ratios.has_all_bad_chirality_c = (
        raw_data.summary_counts.has_all_bad_chirality_c / raw_data.motive_count
    )
    protein_data.ligand_quality_ratios.missing_atoms = raw_data.summary_counts.missing_atoms / raw_data.motive_count
    protein_data.ligand_quality_ratios.missing_rings = raw_data.summary_counts.missing_rings / raw_data.motive_count
    protein_data.ligand_quality_ratios.missing_atoms_and_rings = missing_atoms_and_rings / raw_data.motive_count
