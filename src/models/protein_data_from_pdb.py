from dataclasses import dataclass, fields
from typing import Optional


@dataclass(slots=True)
class ProteinDataFromPDB:
    pdb_id: Optional[str] = None
    # general counts
    atom_count_without_hetatms: int = 0
    aa_count: Optional[int] = None
    all_atom_count: Optional[int] = None
    all_atom_count_ln: Optional[float] = None
    # hetero atom counts
    hetatm_count: int = 0
    hetatm_count_no_water: int = 0
    hetatm_count_metal: int = 0
    hetatm_count_no_metal: Optional[int] = None
    hetatm_count_no_water_no_metal: Optional[int] = None
    # ligand counts
    ligand_count: int = 0
    ligand_count_no_water: int = 0
    ligand_count_metal: int = 0
    ligand_count_no_metal: Optional[int] = None
    ligand_count_no_water_no_metal: Optional[int] = None
    # ligand ratios
    ligand_ratio: Optional[float] = None
    ligand_ratio_no_water: Optional[float] = None
    ligand_ratio_metal: Optional[float] = None
    ligand_ratio_no_metal: Optional[float] = None
    ligand_ratio_no_water_no_metal: Optional[float] = None
    # weights
    structure_weight: Optional[float] = None
    polymer_weight: Optional[float] = None
    nonpolymer_weight: Optional[float] = None
    nonpolymer_weight_no_water: Optional[float] = None
    water_weight: Optional[float] = None
