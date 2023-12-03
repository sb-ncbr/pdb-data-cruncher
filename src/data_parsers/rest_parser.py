from typing import Any, Optional
import logging

from src.models.ligand_info import LigandInfo
from src.exception import RestParsingError


def parse_rest(pdb_id: str,
               protein_summary_json: dict[str, Any],
               protein_assembly_json: dict[str, Any],
               ligand_infos: dict[str, LigandInfo]) -> bool:
    logging.debug("[%s] Start parsing rest.", pdb_id)
    try:
        parse_rest_unsafe(pdb_id, protein_summary_json, protein_assembly_json, ligand_infos)
        logging.debug("[%s] Rest parsed successfully", pdb_id)
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
    noncritical_issues = []

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
                               f"was not found in assembly json.")

    collected_protein_data["molecular_weight"] = preferred_assembly_full.get("molecular_weight", None)

    for entity in preferred_assembly_full.get("entities", []):
        try:
            entity_id = int(entity["entity_id"])
            molecule_type = entity["molecule_type"].lower()  # lower for case insensitive comparisons
            number_of_copies = int(entity["number_of_copies"])
        except KeyError:
            noncritical_issues.append("Entity in assembly json is missing entity_id, molecule_type or number_of_copies."
                                      f"Skipped. (entity content: {entity})")
            continue
        except ValueError:
            noncritical_issues.append("Entity in assembly json has non-int value as entity_id or number_of_copies."
                                      f"Skipped. (entity content: {entity}")
            continue

        molecule_type = molecule_type.lower()  # change to lowercase for case insensitive comparison
        if molecule_type in ["carbohydrate polymer",
                             "polypeptide(l)",
                             "polypeptide(d)",
                             "polyribonucleotide",
                             "polydeoxyribonucleotide",
                             "polysaccharide(d)",
                             "polysaccharide(l)",
                             "polydeoxyribonucleotide/polyribonucleotide hybrid",
                             "cyclic-pseudo-peptide",
                             "peptide nucleic acid"]:
            biopolymer_entity_count[entity_id] = number_of_copies
        elif molecule_type == "bound":
            ligand_entity_count[entity_id] = number_of_copies
        elif molecule_type == "water":
            water_entity_count[entity_id] = number_of_copies
        elif molecule_type == "other":
            pass  # ignore "other" type
        else:
            noncritical_issues.append(f"Entity {entity_id} in assembly json has unknown type '{molecule_type}'. "
                                      f"Skipped.")

    collected_protein_data["assembly_biopolymer_count"] = sum(biopolymer_entity_count.values())
    collected_protein_data["assembly_ligand_count"] = sum(ligand_entity_count.values())
    collected_protein_data["assembly_water_count"] = sum(water_entity_count.values())
    collected_protein_data["assembly_unique_biopolymer_count"] = len(biopolymer_entity_count)
    collected_protein_data["assembly_unique_ligand_count"] = len(ligand_entity_count)

    # end of processing assembly

    # start of processing molecules json
    # TODO continue Entry.cpp line 425


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
