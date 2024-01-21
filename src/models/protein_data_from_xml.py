from dataclasses import dataclass
from typing import Optional


@dataclass
class ProteinDataFromXML:
    pdb_id: Optional[str] = None

    highest_chain_bonds_RMSZ: Optional[float] = None
    highest_chain_angles_RMSZ: Optional[float] = None
    average_residue_RSR: Optional[float] = None
    average_residue_RSCC: Optional[float] = None
    residue_RSCC_outlier_ratio: Optional[float] = None
    average_ligand_RSR: Optional[float] = None
    average_ligand_RSCC: Optional[float] = None
    ligand_RSCC_outlier_ratio: Optional[float] = None
    average_ligand_angle_RMSZ: Optional[float] = None
    average_ligand_bond_RMSZ: Optional[float] = None
    average_ligand_RSCC_small_ligands: Optional[float] = None
    average_ligand_RSCC_large_ligands: Optional[float] = None
