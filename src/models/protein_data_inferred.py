from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ProteinDataInferred:
    aa_ligand_count: Optional[int] = None
    aa_ligand_count_no_water: Optional[int] = None
    aa_ligand_count_filtered: Optional[int] = None
    combined_geometry_quality: Optional[float] = None
    combined_x_ray_quality_metric: Optional[float] = None
    combined_overall_quality_metric: Optional[float] = None
    resolution: Optional[float] = None
