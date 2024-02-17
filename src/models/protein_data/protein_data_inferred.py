from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ProteinDataInferred:
    """
    Class holding protein data calculated from other collected protein data.
    """

    aa_ligand_count_filtered: Optional[int] = None
    combined_geometry_quality: Optional[float] = None
    combined_x_ray_quality_metric: Optional[float] = None
    combined_overall_quality_metric: Optional[float] = None
