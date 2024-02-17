import logging
from dataclasses import dataclass
from typing import Optional
from xml.etree.ElementTree import Element, ParseError
from xml.etree.ElementTree import parse as parse_element_tree

from src.models import ProteinDataFromXML, Diagnostics, LigandInfo, XML_ENTRY_ATTRIBUTE_TO_PROPERTY
from src.utils import to_float, to_int, get_clean_type_hint


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class ModelledSubgroupsData:
    """
    Class holding information extracted from ModelledSubgroup elements form XML, to be processed into protein data.
    """

    # residue related data
    residue_count: int = 0
    residue_rscc_outlier_count: int = 0
    residue_rsr_sum: float = 0.0
    residue_rscc_sum: float = 0.0
    has_residue_rsr: bool = False
    has_residue_rscc: bool = False
    # ligand related data
    ligand_count: int = 0
    ligand_count_10_and_below: int = 0
    ligand_count_11_and_above: int = 0
    ligand_rscc_outlier_count: int = 0
    ligand_rmsz_sum_angles: float = 0.0
    ligand_rmsz_sum_bonds: float = 0.0
    ligand_rsr_sum: float = 0.0
    ligand_rscc_sum: float = 0.0
    ligand_rscc_sum_10_and_below: float = 0.0
    ligand_rscc_sum_11_and_above: float = 0.0
    has_ligand_rmsz_angles: bool = False
    has_ligand_rsr: bool = False
    has_ligand_rscc: bool = False
    has_ligand_rscc_sum_10_and_below: bool = False
    has_ligand_rscc_sum_11_and_above: bool = False


def parse_xml_validation_report(
    pdb_id: str, filepath: str, ligand_info: dict[str, LigandInfo]
) -> Optional[ProteinDataFromXML]:
    """
    Extracts and calculates protein information from given XML validation file.
    :param pdb_id: PDB ID to extract.
    :param filepath: Path to the xml validation report file.
    :param ligand_info: Loaded ligand stats.
    :return: Collected protein data.
    """
    logging.debug("[%s] XML validation report parsing started. Will extract xml file from: %s", pdb_id, filepath)
    try:
        protein_data, diagnostics = _parse_xml_validation_report_unsafe(pdb_id, filepath, ligand_info)
        diagnostics.process_into_logging("XML parsing", pdb_id)
        return protein_data
    except OSError as ex:  # Issue with opening given file
        logging.info("[%s] %s", pdb_id, ex)  # only INFO - some structures may not have XML validation and that's ok
        return None
    except ParseError as ex:  # XML parsing error
        logging.error("[%s] %s", pdb_id, ex)
        return None
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # Catching all unexpected exceptions to allow the rest of program to continue
        logging.exception("[%s] XML parsing: Encountered unexpected issue: %s", pdb_id, ex)
        return None


def _parse_xml_validation_report_unsafe(
    pdb_id: str, filepath: str, ligand_infos: dict[str, LigandInfo]
) -> tuple[Optional[ProteinDataFromXML], Diagnostics]:
    """
    Extracts and calculates protein information from given XML validation file. Unsafe - can raise exceptions.
    :param pdb_id: PDB ID of protein to extract.
    :param filepath: Path to the xml file representing validation report.
    :param ligand_infos: Dictionary with general ligand information.
    :return: Collected protein data and diagnostics about non-critical data issues.
    """
    xml_tree = parse_element_tree(filepath)
    protein_data = ProteinDataFromXML(pdb_id=pdb_id)
    diagnostics = Diagnostics()

    entry_element = xml_tree.find("Entry")
    _extract_entry_information(entry_element, protein_data, diagnostics)
    modelled_subgroups = xml_tree.findall("ModelledSubgroup")
    _process_modelled_subgroups(modelled_subgroups, ligand_infos, protein_data, diagnostics)
    modelled_entity_instances = xml_tree.findall("ModelledEntityInstance")
    _process_modelled_entity_instances(modelled_entity_instances, protein_data, diagnostics)

    return protein_data, diagnostics


def _extract_entry_information(
    entry_element: Optional[Element], protein_data: ProteinDataFromXML, diagnostics: Diagnostics
) -> None:
    """
    Extracts and saves straightforward data from entry element based on constant dictionary mapping the
    name of elements to name of protein data field.
    :param entry_element: XML element Entry.
    :param protein_data: Data to which information is collected.
    :param diagnostics: Collected information about non-critical issues.
    """
    if entry_element is None:
        diagnostics.add("No 'Entry' element present in XML.")
        return

    clashscore = to_float(entry_element.get("clashscore"))
    if clashscore is not None and clashscore != -1.0:  # -1.0 is value that makes no sense for clashscore
        protein_data.clashscore = clashscore

    # for each attribute, it extracts it, retypes if neccessary, and stores into protein data
    for xml_attribute_name, protein_data_field_name in XML_ENTRY_ATTRIBUTE_TO_PROPERTY.items():
        attribute_value = entry_element.get(xml_attribute_name)
        if attribute_value is None or attribute_value == "NotAvailable":
            continue

        protein_data_item_type = get_clean_type_hint(protein_data, protein_data_field_name)
        if protein_data_item_type == int:
            attribute_value = to_int(attribute_value)
            if attribute_value is None:
                diagnostics.add(
                    f"Entry attribute {xml_attribute_name} failed to convert to int. "
                    f"(value: {entry_element.get(xml_attribute_name)})"
                )
        elif protein_data_item_type == float:
            attribute_value = to_float(attribute_value)
            if attribute_value is None:
                diagnostics.add(
                    f"Entry attribute {xml_attribute_name} failed to convert to float. "
                    f"(value: {entry_element.get(xml_attribute_name)})"
                )

        try:
            setattr(protein_data, protein_data_field_name, attribute_value)  # sets relevant field of protein data
        except AttributeError as ex:
            diagnostics.add(f"Entry attribute could not be saved to protein data: {ex}")


def _process_modelled_subgroups(
    modelled_subgroups: list[Element],
    ligand_infos: dict[str, LigandInfo],
    protein_data: ProteinDataFromXML,
    diagnostics: Diagnostics,
):
    """
    Process all elements from XML that are ModelledSubgroup. Gather desired protein data form them.
    :param modelled_subgroups: List of XML elements ModelledSubgroup.
    :param ligand_infos: Dictionary holding general ligand information.
    :param protein_data: Class holding extracted protein data.
    :param diagnostics: Class holding diagnostics about non-critical data issues.
    """
    subgroups_data = ModelledSubgroupsData()

    # collect data from the xml elements
    for element in modelled_subgroups:
        if "mogul_bonds_rmsz" in element.attrib:  # it is ligand
            _process_ligand_modelled_subgroup(element, subgroups_data, ligand_infos, diagnostics)
        else:  # it is not ligand
            _process_residue_modelled_subgroup(element, subgroups_data, diagnostics)

    # process collected data into protein data we are interested in
    _process_subgroups_data_into_protein_data(subgroups_data, protein_data)


def _process_subgroups_data_into_protein_data(
    subgroups_data: ModelledSubgroupsData, protein_data: ProteinDataFromXML
) -> None:
    """
    Process collected ModelledSubgroupsData into protein data we are interested in.
    :param subgroups_data: Collected model subgroup data.
    :param protein_data: Dataclass for holding protein data to be extracted.
    """
    if subgroups_data.residue_count > 0:
        if subgroups_data.has_residue_rsr:
            protein_data.average_residue_rsr = subgroups_data.residue_rsr_sum / subgroups_data.residue_count
        if subgroups_data.has_residue_rscc:
            protein_data.average_residue_rscc = subgroups_data.residue_rscc_sum / subgroups_data.residue_count
            protein_data.residue_rscc_outlier_ratio = (
                subgroups_data.residue_rscc_outlier_count / subgroups_data.residue_count
            )

    if subgroups_data.ligand_count > 0:
        protein_data.average_ligand_bond_rmsz = subgroups_data.ligand_rmsz_sum_bonds / subgroups_data.ligand_count
        if subgroups_data.has_ligand_rsr:
            protein_data.average_ligand_rsr = subgroups_data.ligand_rsr_sum / subgroups_data.ligand_count
        if subgroups_data.has_ligand_rscc:
            protein_data.average_ligand_rscc = subgroups_data.ligand_rscc_sum / subgroups_data.ligand_count
            protein_data.ligand_rscc_outlier_ratio = (
                subgroups_data.ligand_rscc_outlier_count / subgroups_data.ligand_count
            )
        if subgroups_data.has_ligand_rmsz_angles:
            protein_data.average_ligand_angle_rmsz = subgroups_data.ligand_rmsz_sum_angles / subgroups_data.ligand_count

    if subgroups_data.ligand_count_10_and_below > 0 and subgroups_data.has_ligand_rscc_sum_10_and_below:
        protein_data.average_ligand_rscc_small_ligands = (
            subgroups_data.ligand_rscc_sum_10_and_below / subgroups_data.ligand_count_10_and_below
        )

    if subgroups_data.ligand_count_11_and_above > 0 and subgroups_data.has_ligand_rscc_sum_11_and_above:
        protein_data.average_ligand_rscc_large_ligands = (
            subgroups_data.ligand_rscc_sum_11_and_above / subgroups_data.ligand_count_11_and_above
        )


def _process_ligand_modelled_subgroup(
    element: Element,
    subgroups_data: ModelledSubgroupsData,
    ligand_infos: dict[str, LigandInfo],
    diagnostics: Diagnostics,
) -> None:
    """
    Process one element from XML that is ModelledSubgroup and is ligand, not residue.
    :param element: XML element to process.
    :param subgroups_data: Dataclass holding the data collected so far, to which this elements info is to be added.
    :param ligand_infos: Dictionary holding general ligand information.
    :param diagnostics: Class holding diagnostics about non-critical data issues.
    """
    subgroups_data.ligand_count += 1
    _process_subgroup_mogul_bonds_rmsz(element, subgroups_data, diagnostics)
    _process_subgroup_mogul_angles_rmsz(element, subgroups_data, diagnostics)
    _process_subgroup_rsr(element, subgroups_data, diagnostics)
    rscc = _process_subgroups_rscc(element, subgroups_data, diagnostics)
    _process_subgroup_ligand_sizes(element, subgroups_data, rscc, ligand_infos, diagnostics)


def _process_subgroup_mogul_bonds_rmsz(
    element: Element, subgroups_data: ModelledSubgroupsData, diagnostics: Diagnostics
) -> None:
    """
    Process the part of ModelledSubgroup element related to "mogul_bonds_rmsz" attribute.
    :param element: XML element ModelledSubgroup.
    :param subgroups_data: Data from this ModelledSubgroup collected so far, to which information is added.
    :param diagnostics: Class holding diagnostics about non-ciritical data issues.
    """
    mogul_bonds_rmsz = to_float(element.get("mogul_bonds_rmsz"))
    if mogul_bonds_rmsz is not None:
        subgroups_data.ligand_rmsz_sum_bonds += mogul_bonds_rmsz
    else:
        _record_extraction_failure(diagnostics, element, "mogul_bonds_rmsz")


def _process_subgroup_mogul_angles_rmsz(
    element: Element, subgroups_data: ModelledSubgroupsData, diagnostics: Diagnostics
):
    """
    Process the part of ModelledSubgroup element related to "mogul_bonds_rmsz" attribute.
    :param element: XML element ModelledSubgroup.
    :param subgroups_data: Data from this ModelledSubgroup collected so far, to which information is added.
    :param diagnostics: Class holding diagnostics about non-ciritical data issues.
    """
    if "mogul_angles_rmsz" in element.attrib:
        mogul_angles_rmsz = to_float(element.get("mogul_angles_rmsz"))
        if mogul_angles_rmsz is not None:
            subgroups_data.has_ligand_rmsz_angles = True
            subgroups_data.ligand_rmsz_sum_angles += mogul_angles_rmsz
        else:
            _record_extraction_failure(diagnostics, element, "mogul_angles_rmsz")


def _process_subgroup_rsr(element: Element, subgroups_data: ModelledSubgroupsData, diagnostics: Diagnostics) -> None:
    """
    Process the part of ModelledSubgroup element related to "rsr" attribute.
    :param element: XML element ModelledSubgroup.
    :param subgroups_data: Data from this ModelledSubgroup collected so far, to which information is added.
    :param diagnostics: Class holding diagnostics about non-ciritical data issues.
    """
    if "rsr" in element.attrib:
        rsr = to_float(element.get("rsr"))
        if rsr is not None:
            subgroups_data.has_ligand_rsr = True
            subgroups_data.ligand_rsr_sum += rsr
        else:
            _record_extraction_failure(diagnostics, element, "rsr")


def _process_subgroups_rscc(
    element: Element, subgroups_data: ModelledSubgroupsData, diagnostics: Diagnostics
) -> Optional[float]:
    """
    Process the part of ModelledSubgroup element related to "rscc" attribute.
    :param element: XML element ModelledSubgroup.
    :param subgroups_data: Data from this ModelledSubgroup collected so far, to which information is added.
    :param diagnostics: Class holding diagnostics about non-ciritical data issues.
    :return: Float representing extracted rscc value, or None if not present.
    """
    rscc = None
    if "rscc" in element.attrib:
        rscc = to_float(element.get("rscc"))
        if rscc is not None:
            subgroups_data.has_ligand_rscc = True
            subgroups_data.ligand_rscc_sum += rscc
            if rscc < 0.8:
                subgroups_data.ligand_rscc_outlier_count += 1
        else:
            _record_extraction_failure(diagnostics, element, "rscc")
    return rscc


def _process_subgroup_ligand_sizes(
    element: Element,
    subgroups_data: ModelledSubgroupsData,
    rscc: float,
    ligand_infos: dict[str, LigandInfo],
    diagnostics: Diagnostics,
):
    """
    Process the part of ModelledSubgroup element related to small and large ligands.
    :param element: XML element ModelledSubgroup.
    :param subgroups_data: Data from this ModelledSubgroup collected so far, to which information is added.
    :param rscc: Value of "rscc" attribute of this element.
    :param ligand_infos: Dictionary holding general ligand information.
    :param diagnostics: Class holding diagnostics about non-ciritical data issues.
    """
    ligand_id = element.get("resname")
    ligand_info = ligand_infos.get(ligand_id)
    if not ligand_id:
        diagnostics.add(
            "Element has no resname, even though it was determined to be ligand because "
            "of mogul_bonds_rmsz presence."
        )
    elif not ligand_info:
        diagnostics.add(f"Ligand with ID '{ligand_id}' was not found in ligand infos.")
    elif ligand_info.heavy_atom_count > 10:
        subgroups_data.ligand_count_11_and_above += 1
        if rscc is not None:
            subgroups_data.ligand_rscc_sum_11_and_above += rscc
            subgroups_data.has_ligand_rscc_sum_11_and_above = True
    else:
        subgroups_data.ligand_count_10_and_below += 1
        if rscc is not None:
            subgroups_data.ligand_rscc_sum_10_and_below += rscc
            subgroups_data.has_ligand_rscc_sum_10_and_below = True


def _process_residue_modelled_subgroup(
    element: Element, subgroups_data: ModelledSubgroupsData, diagnostics: Diagnostics
) -> None:
    """
    Process one element from XML that is ModelledSubgroup and is residue, not ligand.
    :param element: XML element to process.
    :param subgroups_data: Dataclass holding the data collected so far, to which this elements info is to be added.
    :param diagnostics: Class holding diagnostics about non-critical data issues.
    """
    subgroups_data.residue_count += 1

    if "rsr" in element.attrib:
        rsr = to_float(element.get("rsr"))
        if rsr is not None:
            subgroups_data.has_residue_rsr = True
            subgroups_data.residue_rsr_sum += rsr
        else:
            _record_extraction_failure(diagnostics, element, "rsr")

    if "rscc" in element.attrib:
        rscc = to_float(element.get("rscc"))
        if rscc is not None:
            subgroups_data.has_residue_rscc = True
            subgroups_data.residue_rscc_sum += rscc
            if rscc < 0.8:
                subgroups_data.residue_rscc_outlier_count += 1
        else:
            _record_extraction_failure(diagnostics, element, "rscc")


def _process_modelled_entity_instances(
    modelled_entity_instances: list[Element], protein_data: ProteinDataFromXML, diagnostics: Diagnostics
) -> None:
    """
    Process all elements from XML that are ModelledEntityInstance. Gather desired protein data form them.
    :param modelled_entity_instances: List of XML elements ModelledEntityInstance.
    :param protein_data: Class holding already extracted protein data.
    :param diagnostics: Class holding diagnostics about non-critical data issues.
    """
    highest_chain_bonds_rmsz = None
    highest_chain_angles_rmsz = None

    for element in modelled_entity_instances:
        if "bonds_rmsz" in element.attrib:
            bonds_rmsz = to_float(element.get("bonds_rmsz"))
            if bonds_rmsz is None:
                _record_extraction_failure(diagnostics, element, "bonds_rmsz")
            elif highest_chain_bonds_rmsz is None or bonds_rmsz > highest_chain_bonds_rmsz:
                highest_chain_bonds_rmsz = bonds_rmsz

        if "angles_rmsz" in element.attrib:
            angles_rmsz = to_float(element.get("angles_rmsz"))
            if angles_rmsz is None:
                _record_extraction_failure(diagnostics, element, "angles_rmsz")
            elif highest_chain_angles_rmsz is None or angles_rmsz > highest_chain_angles_rmsz:
                highest_chain_angles_rmsz = angles_rmsz

    protein_data.highest_chain_bonds_rmsz = highest_chain_bonds_rmsz
    protein_data.highest_chain_angles_rmsz = highest_chain_angles_rmsz


def _record_extraction_failure(diagnostics: Diagnostics, element: Element, attribute_name: str) -> None:
    """
    Creates a new issue in diagnostic with information about the attribute that failed to extract from the element.
    :param diagnostics: Class holding diagnostics about current issues.
    :param element: Element that the attribute is extracted from.
    :param attribute_name: Name of the attribute that failed to extract.
    """
    diagnostics.add(f"Attribue {attribute_name} failed to convert to float. " f"Value: '{element.get(attribute_name)}'")
