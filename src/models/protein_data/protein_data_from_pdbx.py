from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class ProteinDataFromPDBx:
    """
    Class holding data about protein extracted from pdbx files.
    """

    pdb_id: Optional[str] = None
    # general counts
    atom_count_without_hetatms: int = 0
    aa_count: int = 0
    aa_ligand_count: Optional[int] = None
    aa_ligand_count_no_water: Optional[int] = None
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
    structure_weight_kda: Optional[float] = None
    polymer_weight_kda: float = 0.0
    nonpolymer_weight_no_water_da: float = 0.0
    water_weight_da: float = 0.0
    nonpolymer_weight_da: Optional[float] = None
    # other
    resolution: Optional[float] = None
    experimental_method: Optional[str] = None  # _exptl.method
    ligand_types_present: set[str] = field(default_factory=set)
