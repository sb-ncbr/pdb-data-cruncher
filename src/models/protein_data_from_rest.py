from dataclasses import dataclass, fields
from typing import Optional


@dataclass(slots=True)
class ProteinDataFromRest:
    pdb_id: Optional[str] = None
    release_date: Optional[str] = None
    experimental_method_class: Optional[str] = None
    submission_site: Optional[str] = None
    processing_site: Optional[str] = None
    molecular_weight: Optional[float] = None
    assembly_biopolymer_count: Optional[int] = None
    assembly_ligand_count: Optional[int] = None
    assembly_water_count: Optional[int] = None
    assembly_unique_biopolymer_count: Optional[int] = None
    assembly_unique_ligand_count: Optional[int] = None
    assembly_biopolymer_weight: Optional[float] = None
    assembly_ligand_weight: Optional[float] = None
    assembly_water_weight: Optional[float] = None
    assembly_ligand_flexibility: Optional[float] = None

    @property
    def values_missing(self):
        return sum(field is None for field in fields(self))
