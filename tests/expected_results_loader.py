import csv
from dataclasses import dataclass, asdict
from typing import get_type_hints, Optional

from tests.test_constants import CRUNCHED_RESULTS_CSV_PATH
from src.models.protein_data import (
    ProteinDataFromXML,
    ProteinDataFromVDB,
    ProteinDataFromPDBx,
    ProteinDataFromRest,
    ProteinDataInferred,
    ProteinDataComplete,
)
from src.utils import to_int, to_float
from src.models import CSV_OUTPUT_ATTRIBUTE_NAMES, CSV_ATTRIBUTE_ORDER


def load_first_and_relevant_row_from_csv(pdb_id: str) -> tuple[list[str], list[str]]:
    with open(CRUNCHED_RESULTS_CSV_PATH, encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        first_row = next(csv_reader)
        relevant_row = None
        current_row = next(csv_reader)
        while current_row:
            if current_row[0] == pdb_id:
                relevant_row = current_row
                break
            current_row = next(csv_reader)

        if not relevant_row:
            raise RuntimeError(f"Row with pdb_id {pdb_id} not found in csv file.")

    return first_row, relevant_row


def load_row_of_csv_as_dict(pdb_id: str) -> dict[str, str]:
    row_as_dict = {}
    first_row, relevant_row = load_first_and_relevant_row_from_csv(pdb_id)
    for header_name, value in zip(first_row, relevant_row):
        if header_name:
            row_as_dict[header_name] = value
    return row_as_dict


def load_chosen_items_from_crunched_results_csv(pdb_id: str, fields: list[str]) -> dict[str, str]:
    """
    Loads data from crunched_results.csv and returns only relevant field values.
    :param pdb_id: PDB ID of structure data to load.
    :param fields: Fields to exctract.
    :return: Dict where keys are given field names, and values are extracted values (as strings).
    :raises RuntimeError: If PDB ID is not found in csv or one or more fields are not found.
    """
    first_row, relevant_row = load_first_and_relevant_row_from_csv(pdb_id)

    extracted_fields = {}
    for index, field_name in enumerate(first_row):
        if field_name in fields:
            if relevant_row[index] == "nan":
                extracted_fields[field_name] = None
            else:
                extracted_fields[field_name] = relevant_row[index]

    if len(extracted_fields) != len(fields):
        not_found_fields = [field_name for field_name in fields if field_name not in extracted_fields]
        raise RuntimeError(f"{len(not_found_fields)} fields not found in csv file: {not_found_fields}")

    return extracted_fields


def find_field_name_in_csv_attributes(searched_attribute_name: str):
    for field_name, attribute_name in CSV_OUTPUT_ATTRIBUTE_NAMES.items():
        if attribute_name == searched_attribute_name:
            return field_name


def fill_protein_data_with_crunched_csv_data(pdb_id: str, protein_data: dataclass) -> None:
    """
    Loads fields into dataclass protein data from crunched csv based on the attribute and field names. The field does
    not get loaded if the translation is not included in CSV_OUTPUT_ATTRIBUTES_NAMES.
    :param pdb_id: Protein id.
    :param protein_data: Protein data class to load info into (has to be one of the basic ones, not complete).
    """
    csv_attributes_to_extract = {}
    typing_hints = get_type_hints(protein_data)
    for field_name in asdict(protein_data).keys():  # for every field in given dataclass
        if field_name in CSV_OUTPUT_ATTRIBUTE_NAMES:  # if that field is in csv output names
            expected_type = typing_hints[field_name]  # get its type based on type hints
            type_into = None
            if expected_type == float or expected_type == Optional[float]:
                type_into = float
            elif expected_type == int or expected_type == Optional[int]:
                type_into = int
            attribute_name = CSV_OUTPUT_ATTRIBUTE_NAMES[field_name]
            csv_attributes_to_extract[attribute_name] = type_into  # and save it for extraction

    data = load_chosen_items_from_crunched_results_csv(pdb_id, list(csv_attributes_to_extract.keys()))
    for csv_attribute_name, type_into in csv_attributes_to_extract.items():
        value = data[csv_attribute_name]
        if type_into == int:
            value = to_int(value)
        if type_into == float:
            value = to_float(value)
        field_name = find_field_name_in_csv_attributes(csv_attribute_name)
        setattr(protein_data, field_name, value)  # set attribute with that name in protein data


def load_expected_pdbx_protein_data(pdb_id: str):
    protein_data = ProteinDataFromPDBx(pdb_id=pdb_id)
    fill_protein_data_with_crunched_csv_data(pdb_id, protein_data)
    return protein_data


def load_expected_rest_protein_data(pdb_id: str) -> ProteinDataFromRest:
    protein_data = ProteinDataFromRest(pdb_id=pdb_id)
    fill_protein_data_with_crunched_csv_data(pdb_id, protein_data)
    return protein_data


def load_expected_validator_db_protein_data(pdb_id: str) -> ProteinDataFromVDB:
    protein_data = ProteinDataFromVDB(pdb_id=pdb_id)
    fill_protein_data_with_crunched_csv_data(pdb_id, protein_data)
    return protein_data


def load_expected_xml_protein_data(pdb_id: str) -> ProteinDataFromXML:
    protein_data = ProteinDataFromXML(pdb_id=pdb_id)
    fill_protein_data_with_crunched_csv_data(pdb_id, protein_data)
    return protein_data


def load_expected_inferred_data(pdb_id: str) -> ProteinDataInferred:
    protein_data = ProteinDataInferred()
    fill_protein_data_with_crunched_csv_data(pdb_id, protein_data)
    return protein_data


def load_complete_protein_data(pdb_id: str) -> ProteinDataComplete:
    return ProteinDataComplete(
        pdb_id=pdb_id,
        pdbx=load_expected_pdbx_protein_data(pdb_id),
        rest=load_expected_rest_protein_data(pdb_id),
        vdb=load_expected_validator_db_protein_data(pdb_id),
        xml=load_expected_xml_protein_data(pdb_id),
        inferred=load_expected_inferred_data(pdb_id),
    )
