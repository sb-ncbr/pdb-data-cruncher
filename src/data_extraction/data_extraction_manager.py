import logging
from multiprocessing import Pool
from os import path
from typing import Optional

import pandas as pd

from src.config import Config
from src.models import LigandInfo
from src.models.names_csv_output_attributes import CRUNCHED_CSV_FACTOR_ORDER
from src.models.protein_data import (
    ProteinDataFromRest,
    ProteinDataFromPDBx,
    ProteinDataFromXML,
    ProteinDataFromVDB,
    ProteinDataComplete,
)
from src.generic_file_handlers.json_file_loader import load_json_file
from src.generic_file_handlers.json_file_writer import write_json_file
from src.data_extraction.crunched_data_csv_writer import create_csv_crunched_data, create_xlsx_crunched_data
from src.data_extraction.ligand_stats_parser import parse_ligand_stats
from src.data_extraction.rest_parser import parse_rest
from src.data_extraction.pdbx_parser import parse_pdbx
from src.data_extraction.xml_validation_report_parser import parse_xml_validation_report
from src.data_extraction.validator_db_result_parser import parse_validator_db_result
from src.data_extraction.inferred_protein_data_calculator import calculate_inferred_protein_data
from src.data_extraction.pdb_ids_to_update_finder import find_pdb_ids_to_update
from src.data_extraction.ligand_occurance_handler import update_ligand_occurence_in_structures
from src.exception import ParsingError, FileWritingError


class DataExtractionManager:
    """
    Class with static methods only aggregating file loading and parsing operations into logical groups
    for easier handling.
    """

    @staticmethod
    def load_and_parse_ligand_stats(config: Config) -> Optional[dict[str, LigandInfo]]:
        """
        Load and parse ligand stats csv.
        :param config: App configuration (with valid path_to_ligand_stats_csv).
        :return: Loaded ligand information, or None in case of serious error.
        """
        try:
            return parse_ligand_stats(config.filepaths.ligand_stats)
        except OSError as ex:
            logging.error("Loading ligand stats failed: %s! All values requiring them will be none.", ex)
            return {}

    @staticmethod
    def load_and_parse_rest(
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
        summary_json_path = path.join(config.filepaths.rest_jsons, "summary", f"{pdb_id}.json")
        assembly_json_path = path.join(config.filepaths.rest_jsons, "assembly", f"{pdb_id}.json")
        molecules_json_path = path.join(config.filepaths.rest_jsons, "molecules", f"{pdb_id}.json")
        try:
            protein_summary_json = load_json_file(summary_json_path)
            protein_assembly_json = load_json_file(assembly_json_path)
            protein_molecules_json = load_json_file(molecules_json_path)
        except ParsingError as ex:
            logging.error("[%s] Loading rest json files failed: %s", pdb_id, ex)
            return None

        return parse_rest(pdb_id, protein_summary_json, protein_assembly_json, protein_molecules_json, ligand_info)

    @staticmethod
    def load_and_parse_pdbx(pdb_id: str, config: Config) -> Optional[ProteinDataFromPDBx]:
        """
        Assembles path of mmcif file from pdb id and config, attempts to load it and process it into protein
        data instance.
        :param pdb_id: PDB ID of protein to process.
        :param config: App configuration.
        :return: Instance of ProteinDataFromPDBx loaded with protein data, or None in case of a serious error.
        """
        filepath = path.join(config.filepaths.pdb_mmcifs, f"{pdb_id}.cif")
        return parse_pdbx(pdb_id, filepath)

    @staticmethod
    def load_and_parse_xml_validation_report(
        pdb_id: str, ligand_info: dict[str, LigandInfo], config: Config
    ) -> Optional[ProteinDataFromXML]:
        """
        Attempts to load xml validation report file and extract relevant infromation from it.
        :param pdb_id: Id of the protein.
        :param ligand_info: Dictionary containing ligand information.
        :param config: App configuration containing paths where to look for the file.
        :return: Protein information in case of success, None in case of critical issue.
        """
        filepath = path.join(config.filepaths.xml_reports, f"{pdb_id}_validation.xml")
        return parse_xml_validation_report(pdb_id, filepath, ligand_info)

    @staticmethod
    def load_and_parse_validator_db_result(pdb_id: str, config: Config) -> Optional[ProteinDataFromVDB]:
        """
        Attempts to find validator db result.json, load it and extract relevant protein information from it.
        :param pdb_id: Id of the protein.
        :param config: App configuration containing paths where to look for the file.
        :return: Protein information in case of success, None in case of critical issue.
        """
        filepath = path.join(config.filepaths.validator_db_results, pdb_id, "result.json")
        try:
            result_json = load_json_file(filepath)
        except ParsingError as ex:
            logging.info("[%s] Loading VDB result.json file failed: %s", pdb_id, ex)
            return None

        return parse_validator_db_result(pdb_id, result_json)

    @staticmethod
    def load_all_protein_data(
        pdb_id: str, config: Config, ligand_stats: list[LigandInfo] = None
    ) -> ProteinDataComplete:
        """
        Extract all protein data from all the sources.
        :param pdb_id: Protein id.
        :param config: App config.
        :param ligand_stats: (optional) Already loaded ligand stats. If not passed, they are loaded.
        :return: Collected protein data.
        """
        protein_data = ProteinDataComplete(pdb_id=pdb_id)
        if ligand_stats is None:
            ligand_stats = DataExtractionManager.load_and_parse_ligand_stats(config)
        protein_data.vdb = DataExtractionManager.load_and_parse_validator_db_result(pdb_id, config)
        protein_data.pdbx = DataExtractionManager.load_and_parse_pdbx(pdb_id, config)
        protein_data.xml = DataExtractionManager.load_and_parse_xml_validation_report(pdb_id, ligand_stats, config)
        protein_data.rest = DataExtractionManager.load_and_parse_rest(pdb_id, ligand_stats, config)
        calculate_inferred_protein_data(protein_data)
        logging.debug("[%s] All protein data loaded", pdb_id)
        return protein_data

    @staticmethod
    def update_ligand_occurence_json(protein_data_list: list[ProteinDataComplete], config: Config) -> None:
        try:
            ligand_occurence_json = load_json_file(config.filepaths.ligand_occurence_json)
            update_ligand_occurence_in_structures(protein_data_list, ligand_occurence_json)
            write_json_file(config.filepaths.ligand_occurence_json, ligand_occurence_json)
        except (ParsingError, FileWritingError) as ex:
            logging.error("Failed to load ligand occurence json: %s", ex)

    @staticmethod
    def store_protein_data_into_crunched_csv(protein_data_list: list[ProteinDataComplete], config: Config) -> None:
        """
        Takes list of protein data and creates crunched csv from it.
        :param protein_data_list: List of collected ProteinDataComplete.
        :param config: App config.
        :raise IrrecoverableError: If crunched csv cannot be created.
        """
        # prepare data
        protein_data_df_list = [pd.DataFrame([protein_data.as_dict_for_csv()]) for protein_data in protein_data_list]
        # adding empty dataframe with desired column order on the start will ensure this order is in output csv
        protein_data_df_list.insert(0, pd.DataFrame(columns=CRUNCHED_CSV_FACTOR_ORDER))
        protein_data_df = pd.concat(protein_data_df_list, ignore_index=True)
        # save into files
        create_csv_crunched_data(protein_data_df, config.filepaths.output_root_path)
        create_xlsx_crunched_data(protein_data_df, config.filepaths.output_root_path)


def run_data_extraction(config: Config) -> bool:
    """
    Do data extraction for pdb id set (defined by data download phase or config values). Creates crunched csv
    (in 3 versions) and updates ligand occurence across structures.
    :param config: Application configuration.
    :return: True if action succeeded. False otherwise.
    """
    logging.info("Starting data extraction.")
    try:
        pdb_ids_to_update = find_pdb_ids_to_update(config)
    except ParsingError as ex:
        logging.error(ex)
        return False

    ligand_stats = DataExtractionManager.load_and_parse_ligand_stats(config)
    with Pool(config.max_process_count) as p:
        collected_data = p.starmap(
            DataExtractionManager.load_all_protein_data,
            [(pdb_id, config, ligand_stats) for pdb_id in pdb_ids_to_update],
        )

    # TODO let it update only for pdb_ids that did not fail on any level of parsing, download too -
    # filter it here before that step, and log the failed and succeeded count
    DataExtractionManager.update_ligand_occurence_json(collected_data, config)
    # DataExtractionManager.store_protein_data_into_crunched_csv(collected_data, config)
    # TODO success value
    raise NotImplementedError()