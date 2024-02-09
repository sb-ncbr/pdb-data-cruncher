from dataclasses import dataclass
from typing import Optional

from src.models.protein_data_from_vdb import ProteinDataFromVDB
from src.models.protein_data_from_xml import ProteinDataFromXML
from src.models.protein_data_from_rest import ProteinDataFromRest
from src.models.protein_data_from_pdbx import ProteinDataFromPDBx


@dataclass(slots=True)
class ProteinDataComplete:
    pdb_id: str
    data_from_vdb: Optional[ProteinDataFromVDB] = None
    data_from_xml: Optional[ProteinDataFromXML] = None
    data_from_rest: Optional[ProteinDataFromRest] = None
    data_from_pdbx: Optional[ProteinDataFromPDBx] = None
