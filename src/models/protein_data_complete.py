from dataclasses import dataclass
from typing import Optional

from src.models.protein_data_from_vdb import ProteinDataFromVDB
from src.models.protein_data_from_xml import ProteinDataFromXML
from src.models.protein_data_from_rest import ProteinDataFromRest
from src.models.protein_data_from_pdbx import ProteinDataFromPDBx
from src.models.protein_data_inferred import ProteinDataInferred


@dataclass(slots=True)
class ProteinDataComplete:
    pdb_id: str
    vdb: Optional[ProteinDataFromVDB] = None
    xml: Optional[ProteinDataFromXML] = None
    rest: Optional[ProteinDataFromRest] = None
    pdbx: Optional[ProteinDataFromPDBx] = None
    inferred: Optional[ProteinDataInferred] = None
