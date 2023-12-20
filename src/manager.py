import logging
import os.path
from typing import Optional

from src.config import Config
from src.models import ProteinDataFromRest, LigandInfo
from src.data_loaders.json_file_loader import load_json_file
from src.data_parsers.rest_parser import parse_rest
from src.exception import ParsingError


class Manager:
    @staticmethod
    def load_and_parse_json(
            pdb_id: str, ligand_info: dict[str, LigandInfo], config: Config
    ) -> Optional[ProteinDataFromRest]:
        try:
            partial_file_path = os.path.join(config.path_to_rest_jsons, pdb_id)
            protein_summary_json = load_json_file(f"{partial_file_path}_summary.json")
            protein_assembly_json = load_json_file(f"{partial_file_path}_assembly.json")
            protein_molecules_json = load_json_file(f"{partial_file_path}_molecules.json")
        except ParsingError as ex:
            logging.error("[%s] Loading rest json files failed: %s", pdb_id, ex)
            return None

        return parse_rest(pdb_id, protein_summary_json, protein_assembly_json, protein_molecules_json, ligand_info)

