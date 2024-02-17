from dataclasses import dataclass
from typing import Optional


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class ProteinDataFromXML:
    """
    Class for holding protein data collected from XML validation report.
    """

    pdb_id: Optional[str] = None

    clashscore: Optional[float] = None
    percent_rama_outliers: Optional[float] = None
    percent_rota_outliers: Optional[float] = None
    absolute_percentile_clashscore: Optional[float] = None
    relative_percentile_clashscore: Optional[float] = None
    num_pdb_ids_relative_percentile_clashscore: Optional[int] = None
    low_resol_relative_percentile_clashscore: Optional[float] = None
    high_resol_relative_percentile_clashscore: Optional[float] = None
    absolute_percentile_percent_rama_outliers: Optional[float] = None
    relative_percentile_percent_rama_outliers: Optional[float] = None
    num_pdb_ids_relative_percentile_percent_rama_outliers: Optional[int] = None
    low_resol_relative_percentile_percent_rama_outliers: Optional[float] = None
    high_resol_relative_percentile_percent_rama_outliers: Optional[float] = None
    absolute_percentile_percent_rota_outliers: Optional[float] = None
    relative_percentile_percent_rota_outliers: Optional[float] = None
    num_pdb_ids_relative_percentile_percent_rota_outliers: Optional[int] = None
    low_resol_relative_percentile_percent_rota_outliers: Optional[float] = None
    high_resol_relative_percentile_percent_rota_outliers: Optional[float] = None

    angles_rmsz: Optional[float] = None
    bonds_rmsz: Optional[float] = None
    percent_rsrz_outliers: Optional[float] = None
    absolute_percentile_percent_rsrz_outliers: Optional[float] = None
    relative_percentile_percent_rsrz_outliers: Optional[float] = None
    num_pdb_ids_realtive_percentile_percent_rsrz_outliers: Optional[int] = None
    low_resol_relative_percentile_percent_rsrz_outliers: Optional[float] = None
    high_resol_relative_percentile_percent_rsrz_outliers: Optional[float] = None
    dcc_r: Optional[float] = None
    dcc_r_free: Optional[float] = None
    absolute_percentile_dcc_r_free: Optional[float] = None
    relative_percentile_dcc_r_free: Optional[float] = None
    num_pdb_ids_relative_percentile_dcc_r_free: Optional[int] = None
    low_resolution_relative_percentile_dcc_r_free: Optional[float] = None
    high_resolution_relative_percentile_dcc_r_free: Optional[float] = None
    absolute_percentile_rna_suiteness: Optional[float] = None

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
