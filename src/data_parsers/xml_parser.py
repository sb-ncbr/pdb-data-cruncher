import xml.etree.ElementTree as ET
from typing import Optional
from src.models import ProteinDataFromXML


def parse_xml(pdb_id: str, filepath: str) -> Optional[ProteinDataFromXML]:
    pass


def _parse_xml_unsafe(pdb_id: str, filepath: str) -> Optional[ProteinDataFromXML]:
    protein_data = ProteinDataFromXML(pdb_id=pdb_id)
    xml_tree = ET.parse(filepath)

    return protein_data
