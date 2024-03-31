import logging
from multiprocessing import Pool
from os import path
from typing import Optional

import pandas as pd

from src.config import Config
from src.data_extraction.crunched_data_csv_handler import (
    create_csv_crunched_data,
    create_xlsx_crunched_data,
    try_to_load_previous_crunched_df,
)
from src.data_extraction.inferred_protein_data_calculator import calculate_inferred_protein_data
from src.data_extraction.ligand_occurance_handler import (
    update_ligand_occurrence_in_structures,
    remove_structure_from_ligand_occurrence,
)
from src.data_extraction.ligand_stats_parser import parse_ligand_stats
from src.data_extraction.pdb_ids_finder import find_pdb_ids_to_update, find_pdb_ids_to_remove
from src.data_extraction.pdbx_parser import parse_pdbx
from src.data_extraction.rest_parser import parse_rest
from src.data_extraction.validator_db_result_parser import parse_validator_db_result
from src.data_extraction.xml_validation_report_parser import parse_xml_validation_report
from src.exception import ParsingError, FileWritingError
from src.generic_file_handlers.json_file_loader import load_json_file
from src.generic_file_handlers.json_file_writer import write_json_file
from src.models import LigandInfo, FactorType
from src.models.names_csv_output_attributes import CRUNCHED_CSV_FACTOR_ORDER
from src.models.protein_data import (
    ProteinDataFromRest,
    ProteinDataFromPDBx,
    ProteinDataFromXML,
    ProteinDataFromVDB,
    ProteinDataComplete,
)
from src.utils import lists_have_crossover


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
    def update_ligand_occurrence_json(protein_data_list: list[ProteinDataComplete], config: Config) -> bool:
        """
        For every protein data, make sure the ligand occurrence json has the structure's id noted down exactly for
        the ligand names present in the data structure.
        :param protein_data_list:
        :param config:
        :return: True if successful.
        """
        try:
            logging.info("Starting updating of ligand occurrence json file.")
            if config.force_complete_data_extraction:
                ligand_occurrence_json = {}  # start fresh for this run mode
            else:
                ligand_occurrence_json = load_json_file(config.filepaths.ligand_occurrence_json)
            update_ligand_occurrence_in_structures(protein_data_list, ligand_occurrence_json)
            write_json_file(config.filepaths.ligand_occurrence_json, ligand_occurrence_json)
            logging.info("Updating of ligand occurrence json file finished successfully.")
            return True
        except (ParsingError, FileWritingError) as ex:
            logging.error("Failed to update ligand occurence json: %s", ex)
            return False

    @staticmethod
    def remove_structures_from_ligand_occurrence_json(structure_ids: list[str], config: Config) -> bool:
        """
        Remove given structure ids from ligand occurrence json (used if the structure was removed altogether).
        :param structure_ids:
        :param config:
        :return: True if successful.
        """
        try:
            logging.info("Starting removing structures from ligand occurrence json file.")
            ligand_occurrence_json = load_json_file(config.filepaths.ligand_occurrence_json)
            for structure_id in structure_ids:
                remove_structure_from_ligand_occurrence(structure_id, ligand_occurrence_json)
            write_json_file(config.filepaths.ligand_occurrence_json, ligand_occurrence_json)
            logging.info("Removing structures from ligand occurence json file finished successfully.")
            return True
        except (ParsingError, FileWritingError) as ex:
            logging.error("Failed to remove items from ligand occurrence json: %s", ex)
            return False

    @staticmethod
    def store_protein_data_into_crunched_csv(
        protein_data_list: list[ProteinDataComplete], structure_ids_to_remove: list[str], config: Config
    ) -> bool:
        """
        Takes list of protein data and updates crunched csv from it.
        :param protein_data_list: List of collected ProteinDataComplete.
        :param structure_ids_to_remove: List of ids of structures that are no longer desired in the crunched csv
        but may have been in the last version that gets updated.
        :param config: App config.
        """
        # load previous crunched data
        original_df = try_to_load_previous_crunched_df(config)
        if original_df is not None and len(structure_ids_to_remove) > 0:
            original_df = original_df[~original_df[FactorType.PDB_ID.value].isin(structure_ids_to_remove)]
        # prepare data
        protein_data_df_list = [pd.DataFrame([protein_data.as_dict_for_csv()]) for protein_data in protein_data_list]
        # adding empty dataframe with desired column order on the start will ensure this order is in output csv
        protein_data_df_list.insert(0, pd.DataFrame(columns=CRUNCHED_CSV_FACTOR_ORDER))
        protein_data_df = pd.concat(protein_data_df_list, ignore_index=True)
        # if original df was loaded, combine it with protein data df and overwrite duplicates with new values
        if original_df is not None:
            protein_data_df = pd.concat([original_df, protein_data_df]).drop_duplicates(
                subset=[FactorType.PDB_ID.value], keep="last"
            )
        # save into files
        create_csv_crunched_data(protein_data_df, config.filepaths.output_root_path)
        create_xlsx_crunched_data(protein_data_df, config.filepaths.output_root_path)
        return True


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
        pdb_ids_to_remove = find_pdb_ids_to_remove(config)
    except ParsingError as ex:
        logging.error(ex)
        return False

    if lists_have_crossover(pdb_ids_to_update, pdb_ids_to_remove):
        logging.error(
            "PDB IDS to update and remove should never have the same items! Double check the inputs.\nPDB IDS to "
            "update: %s.\nPDB IDS to remove: %s.",
            pdb_ids_to_update,
            pdb_ids_to_remove,
        )
        return False

    ligand_stats = DataExtractionManager.load_and_parse_ligand_stats(config)
    with Pool(config.max_process_count) as p:
        collected_data = p.starmap(
            DataExtractionManager.load_all_protein_data,
            [(pdb_id, config, ligand_stats) for pdb_id in pdb_ids_to_update],
        )

    successful_protein_data, overall_success = _filter_and_log_failed_protein_data(collected_data)

    if len(successful_protein_data) > 0:
        overall_success &= DataExtractionManager.update_ligand_occurrence_json(
            successful_protein_data, config
        )
    if len(pdb_ids_to_remove):
        overall_success &= DataExtractionManager.remove_structures_from_ligand_occurrence_json(
            pdb_ids_to_remove, config
        )
    overall_success &= DataExtractionManager.store_protein_data_into_crunched_csv(
        successful_protein_data, pdb_ids_to_remove, config
    )

    # TODO remove old crunched?
    logging.info("Data extraction %s.", "finished successfully" if overall_success else "failed")
    return overall_success


def _filter_and_log_failed_protein_data(
    protein_data_list: list[ProteinDataComplete]
) -> tuple[list[ProteinDataComplete], bool]:
    """
    Get back only the data considered successfull and bool whether all succeeded, log those that are considered failed.
    :param protein_data_list:
    :return: Tuple consisting of filtered protein data list and bool that is True if all protein data were considered
    successfull.
    """
    failed_pdb_ids = []
    successfull_data_list = []

    for protein_data in protein_data_list:
        if protein_data.successful:
            successfull_data_list.append(protein_data)
        else:
            failed_pdb_ids.append(protein_data.pdb_id)

    if len(failed_pdb_ids) > 0:
        logging.error(
            "%s out of %s pdb ids failed to extract and update. If any succeeded, they are still updated. "
            "The failed ids: %s",
            len(failed_pdb_ids),
            len(protein_data_list),
            ", ".join(failed_pdb_ids)
        )

    return successfull_data_list, len(failed_pdb_ids) == 0
