from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class LigandQualityRatios:
    """
    Class holding different ligand quality ratios.
    """

    analyzed: Optional[float] = None
    not_analyzed: Optional[float] = None
    has_all_good_chirality_c_only: Optional[float] = None
    has_all_bad_chirality_c: Optional[float] = None
    missing_atoms: Optional[float] = None
    missing_rings: Optional[float] = None
    missing_atoms_and_rings: Optional[float] = None


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class ProteinDataFromVDB:
    """
    Class holding information about protein extracted from ValidatorDB result.json.
    """

    pdb_id: Optional[str] = None
    # filtered counts
    hetatm_count_filtered: Optional[int] = 0
    ligand_carbon_chiral_atom_count_filtered: Optional[int] = 0
    ligand_count_filtered: Optional[int] = 0
    hetatm_count_filtered_metal: Optional[int] = 0
    ligand_count_filtered_metal: Optional[int] = 0
    hetatm_count_filtered_no_metal: Optional[int] = None
    ligand_count_filtered_no_metal: Optional[int] = None
    # filtered ratios
    ligand_ratio_filtered: Optional[float] = None
    ligand_ratio_filtered_metal: Optional[float] = None
    ligand_ratio_filtered_no_metal: Optional[float] = None
    # other
    ligand_bond_rotation_freedom: Optional[float] = None
    missing_precise: Optional[float] = None
    chiral_problems_precise: Optional[float] = None
    missing_carbon_chiral_errors_precise: Optional[float] = None
    # additional counts
    analyzed_count: Optional[int] = None
    not_analyzed_count: Optional[int] = None
    has_all_bad_chirality_carbon: Optional[int] = None
    missing_atoms: Optional[int] = None
    missing_rings: Optional[int] = None
    # quality ratios
    ligand_quality_ratios: LigandQualityRatios = field(default_factory=LigandQualityRatios)
