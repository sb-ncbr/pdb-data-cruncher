from typing import Any, Optional
import logging

from src.models import LigandInfo
from src.exception import RestParsingError


def parse_rest(pdb_id: str,
               protein_summary_json: dict[str, Any],
               protein_assembly_json: dict[str, Any],
               ligand_infos: dict[str, LigandInfo]) -> bool:
    logging.debug("[%s] Start parsing rest. Summary json path: '%s'.", pdb_id, protein_summary_json)
    try:
        parse_rest_unsafe(pdb_id, protein_summary_json, protein_assembly_json, ligand_infos)
        logging.debug("[%s] Rest parsed successfully")
        return True
    except RestParsingError as ex:
        logging.error("[%s] %s", pdb_id, ex)
        return False
    except Exception as ex:
        logging.exception("[%s] Encountered unexpected issue: %s", pdb_id, ex)
        return False


# TODO after done, consider being less punishing for some errors (maybe eg. one wrong file with different id doesn't
# mean all are useless
# TODO consider returning loading files into here, esp. after the thing is divided into multiple functions
# it may be more officient to avoid holding the information and just load it straight before processing it
def parse_rest_unsafe(pdb_id: str,
                      protein_summary_json: dict[str, Any],
                      protein_assembly_json: dict[str, Any],
                      ligand_infos: dict[str, LigandInfo]) -> None:
    collected_protein_data = {
        "pdb_id": pdb_id
    }

    preferred_assembly_id = parse_protein_summary(pdb_id, protein_summary_json, collected_protein_data)

    # start of processing protein_assembly_json

    if pdb_id not in protein_summary_json.keys():
        raise RestParsingError("Given assembly json doesn't have currently processed pdb_id.")

    biopolymer_entity_count: dict[int, int] = {}
    ligand_entity_count: dict[int, int] = {}
    water_entity_count: dict[int, int] = {}

    preferred_assembly_full = find_preferred_assembly_by_id(
        pdb_id, preferred_assembly_id, protein_assembly_json
    )
    if preferred_assembly_full is None:
        raise RestParsingError(f"Preferred assembly with assembly id {preferred_assembly_id} "
                               f"was found in assembly json.")

    # TODO continue


def parse_protein_summary(pdb_id, protein_summary_json, collected_protein_data) -> str:
    # check pdbId is the same as expected and structure has just one pdbId key with expected value
    if len(protein_summary_json.keys()) > 1:
        raise RestParsingError("Protein summary has more than one pdbId key.")
    if len(protein_summary_json.get("pdb_id", [])) > 1:
        raise RestParsingError("Protein summary array has more than one object.")
    if pdb_id not in protein_summary_json.keys():
        raise RestParsingError(f"Conflicting pdbIds, expected '{pdb_id}', got keys '{protein_summary_json.keys()} "
                               f"inside summary file.")
    protein_summary_list = protein_summary_json[pdb_id][0]
    # extract basic protein information
    release_date_string = protein_summary_list.get("release_date", None)
    collected_protein_data["release_date"] = (release_date_string[:4]
                                              if release_date_string is not None
                                              else None)
    collected_protein_data["rest_method"] = protein_summary_list["experimental_method_class"][0]
    collected_protein_data["submission_site"] = protein_summary_list["deposition_site"]
    collected_protein_data["processing_site"] = protein_summary_list["processing_site"]

    # collect preferred assembly
    preferred_assembly_summary = None
    for assembly in protein_summary_list.get("assemblies", []):
        if assembly.get("preferred", False):
            preferred_assembly_summary = assembly
            break
    if preferred_assembly_summary is None:
        raise RestParsingError("No preffered assembly found.")

    # find the preferred assembly inside assembly json
    preferred_assembly_id = preferred_assembly_summary.get("assembly_id", None)
    if preferred_assembly_id is None:
        raise RestParsingError("No assembly_id found for preferred assembly in protein summary.")
    return preferred_assembly_id


def find_preferred_assembly_by_id(pdb_id: str,
                                  assembly_id: str,
                                  protein_assembly_json: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Find one assembly with given id inside the whole protein assembly json.
    :param pdb_id: Id of protein.
    :param assembly_id: Id of assembly to find.
    :param protein_assembly_json: Json dictionary with assembly information.
    :return: Dictionary of selected assembly, or None if none was found.
    """
    all_assemblies = protein_assembly_json.get(pdb_id, [])
    for assembly in all_assemblies:
        if assembly.get("assembly_id", None) == assembly_id:
            return assembly
    return None
