from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ProteinDataFromVDB:
    """
    Class holding information about protein extracted from ValidatorDB result.json.
    """

    pdb_id: Optional[str] = None
    # filtered counts
    hetatm_count_filtered: Optional[int] = 0
    ligand_carbon_chira_atom_count_filtered: Optional[int] = 0
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
    chira_problems_precise: Optional[float] = None
    missing_carbon_chira_errors_precise: Optional[float] = None
    # quality ratios
    ligand_quality_ratio_good_chirality_carbon: Optional[float] = None
    ligand_quality_ratio_bad_chirality_carbon: Optional[float] = None
    ligand_quality_missing_atoms_and_rings: Optional[float] = None

    @property
    def ligand_quality_binary_good_chirality_carbon(self) -> Optional[int]:
        """
        Property based on ligand_quality_ratio_good_chirality_carbon.
        :return: 1 if the relevant value is 1.0, 0 otherwise.
        """
        if self.ligand_quality_ratio_good_chirality_carbon is None:
            return None
        if self.ligand_quality_ratio_good_chirality_carbon == 1.0:
            return 1
        return 0

    @property
    def ligand_quality_binary_missing_atoms_and_rings(self) -> Optional[int]:
        """
        Property based on ligand_quality_missing_atoms_and_rings.
        :return: 0 if the relevant value is 0.0, 1 otherwise.
        """
        if self.ligand_quality_missing_atoms_and_rings is None:
            return None
        if self.ligand_quality_missing_atoms_and_rings == 0.0:
            return 0
        return 1

    @property
    def chira_problems_precise_binary(self) -> Optional[int]:
        """
        Property based on chira_problems_precise.
        :return: 0 if the relevant value is 0.0, 1 otherwise.
        """
        if self.chira_problems_precise is None:
            return None
        if self.chira_problems_precise == 0.0:
            return 0
        return 1

    @property
    def missing_precise_binary(self) -> Optional[int]:
        """
        Property based on missing_precise.
        :return: 0 if the relevant value is 0.0, 1 otherwise.
        """
        if self.missing_precise is None:
            return None
        if self.missing_precise == 0.0:
            return 0
        return 1
