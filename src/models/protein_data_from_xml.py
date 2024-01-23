from dataclasses import dataclass
from typing import Optional


# pylint: disable=too-many-instance-attributes
@dataclass
class ProteinDataFromXML:
    """
    Class for holding protein data collected from XML validation report.
    """
    pdb_id: Optional[str] = None

    highest_chain_bonds_rmsz: Optional[float] = None
    highest_chain_angles_rmsz: Optional[float] = None
    average_residue_rsr: Optional[float] = None
    average_residue_rscc: Optional[float] = None
    residue_rscc_outlier_ratio: Optional[float] = None
    average_ligand_rsr: Optional[float] = None
    average_ligand_rscc: Optional[float] = None
    ligand_rscc_outlier_ratio: Optional[float] = None
    average_ligand_angle_rmsz: Optional[float] = None
    average_ligand_bond_rmsz: Optional[float] = None
    average_ligand_rscc_small_ligands: Optional[float] = None
    average_ligand_rscc_large_ligands: Optional[float] = None
