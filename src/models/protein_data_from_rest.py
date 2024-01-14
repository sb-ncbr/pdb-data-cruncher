from dataclasses import dataclass, fields
from typing import Optional


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class ProteinDataFromRest:
    """
    Class holding protein data extracted from REST endpoints.
    """

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
    def values_missing(self) -> int:
        """
        Returns the number of values that are none among the class fields.
        :return: Number of values, that are None.
        """
        return sum(field is None for field in fields(self))
