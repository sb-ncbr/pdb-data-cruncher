import logging
import os.path
from typing import Optional

from src.config import Config
from src.models import ProteinDataFromRest, LigandInfo
from src.data_loaders.json_file_loader import load_json_file
from src.data_parsers.rest_parser import parse_rest
from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.exception import ParsingError


class Manager:
    """
    Class with static methods only aggregating file loading and parsing operations into logical groups
    for easier handling.
    """

    @staticmethod
    def load_and_parse_ligand_stats(config: Config) -> Optional[dict[str, LigandInfo]]:
        """
        Load and parse ligand stats csv.
        :param config: App configuration (with valid path_to_ligand_stats_csv.
        :return: Loaded ligand information, or None in case of serious error.
        """
        try:
            return parse_ligand_stats(config.path_to_ligand_stats_csv)
        except OSError as ex:
            logging.error("Loading ligand stats failed: %s", ex)
            return None

    @staticmethod
    def load_and_parse_json(
        pdb_id: str, ligand_info: dict[str, LigandInfo], config: Config
    ) -> Optional[ProteinDataFromRest]:
        """
        Attempts to find needed rest files with given pdb_id (in location given by config). Then it loads their
        information into an instance with collected protein data.
        :param pdb_id: PDB ID of protein to process.
        :param ligand_info: Dictionary containing ligand information.
        :param config: App configuration.
        :return: Instance of ProteinDataFromRest laoded with protein data, or None in case of serious error.
        """
        try:
            partial_file_path = os.path.join(config.path_to_rest_jsons, pdb_id)
            protein_summary_json = load_json_file(f"{partial_file_path}_summary.json")
            protein_assembly_json = load_json_file(f"{partial_file_path}_assembly.json")
            protein_molecules_json = load_json_file(f"{partial_file_path}_molecules.json")
        except ParsingError as ex:
            logging.error("[%s] Loading rest json files failed: %s", pdb_id, ex)
            return None

        return parse_rest(pdb_id, protein_summary_json, protein_assembly_json, protein_molecules_json, ligand_info)
