from dataclasses import dataclass
from typing import Optional
import logging

from src.models.protein_data.protein_data_from_vdb import ProteinDataFromVDB
from src.models.protein_data.protein_data_from_xml import ProteinDataFromXML
from src.models.protein_data.protein_data_from_rest import ProteinDataFromRest
from src.models.protein_data.protein_data_from_pdbx import ProteinDataFromPDBx
from src.models.protein_data.protein_data_inferred import ProteinDataInferred
from src.models.names_csv_output_attributes import CSV_OUTPUT_ATTRIBUTE_NAMES, CSV_INVALID_VALUE_STRING


@dataclass(slots=True)
class ProteinDataComplete:
    """
    Class holding all collected protein data.
    """

    pdb_id: str
    vdb: Optional[ProteinDataFromVDB] = None
    xml: Optional[ProteinDataFromXML] = None
    rest: Optional[ProteinDataFromRest] = None
    pdbx: Optional[ProteinDataFromPDBx] = None
    inferred: Optional[ProteinDataInferred] = None

    @property
    def successful(self):
        return self.rest and self.pdbx

    def as_dict_for_csv(self) -> dict[str, str]:
        """
        Transforms all the data inside the dataclass into a row to be inserted into csv. Uses
        names_csv_output_attributes for mapping field names into expected csv names and for ordering.
        Values are returned as strings, None values are converted to CSV_INVALID_VALUE_STRING.
        :return: List with ordered protein data values.
        """
        csv_row = {}
        for data_field_name, csv_factor_type in CSV_OUTPUT_ATTRIBUTE_NAMES.items():
            value_from_protein_data = self._try_to_get_value(data_field_name)
            if value_from_protein_data is None:
                # should not happen, if values in names_csv_output_attributes.py are properly set
                logging.error(
                    "CODE LOGIC ERROR: Csv attribute %s required by csv_attribute_order isn't included"
                    "in csv_output_names, thus it wasn't extracted. Invalid value assumed.",
                    csv_factor_type.value,
                )
                value_from_protein_data = CSV_INVALID_VALUE_STRING
            csv_row[csv_factor_type.value] = value_from_protein_data
        return csv_row

    def _try_to_get_value(self, field_name) -> Optional[str]:
        """
        Attempts to get given field_name from all the protein data dataclasses inside self.
        :param field_name: Name of the field to extract value from.
        :return: String value of found item, or None in case it failed to find it at all.
        """
        value = self._try_to_get_value_from_one_source(self.pdbx, field_name)
        if value is not None:
            return value
        value = self._try_to_get_value_from_one_source(self.xml, field_name)
        if value is not None:
            return value
        value = self._try_to_get_value_from_one_source(self.rest, field_name)
        if value is not None:
            return value
        value = self._try_to_get_value_from_one_source(self.vdb, field_name)
        if value is not None:
            return value
        value = self._try_to_get_value_from_one_source(self.inferred, field_name)
        if value is not None:
            return value
        # if the code got here, needed value is none of the classes - that can happen in case of completely missing
        # xml validation file, just return invalid value for those
        return CSV_INVALID_VALUE_STRING

    @staticmethod
    def _try_to_get_value_from_one_source(dataclass_to_search: dataclass, field_name: str) -> Optional[str]:
        """
        Attempts to get value from given field from one self protein data dataclass only.
        :param dataclass_to_search: Instance of dataclass with partial protein data.
        :param field_name: Name of field to search for.
        :return: String value of the field value (inc. converting None to string representation),
        or None if the value wasn't found in this dataclass.
        """
        try:
            value = getattr(dataclass_to_search, field_name)
            if value is None:
                return CSV_INVALID_VALUE_STRING
            return str(value)
        except AttributeError:
            return None
