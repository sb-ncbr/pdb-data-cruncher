from xml.etree.ElementTree import parse as parse_element_tree
from xml.etree.ElementTree import Element
from typing import Optional

from src.models import ProteinDataFromXML, Diagnostics, IssueType, LigandInfo
from src.utils import to_float


def parse_xml(pdb_id: str, filepath: str, ligand_info: dict[str, LigandInfo]) -> Optional[ProteinDataFromXML]:
    pass


def _parse_xml_unsafe(
        pdb_id: str, filepath: str, ligand_infos: dict[str, LigandInfo]
) -> tuple[Optional[ProteinDataFromXML], Diagnostics]:
    # TODO check for possible invalid states and logging
    # BTW it is valid to have no data from here i think - it just means the structure is perfect?
    protein_data = ProteinDataFromXML(pdb_id=pdb_id)
    diagnostics = Diagnostics()
    xml_tree = parse_element_tree(filepath)

    # MODELLED SUBGROUPS
    modelled_subgroups = xml_tree.findall("ModelledSubgroup")
    process_modelled_subgroups(modelled_subgroups, ligand_infos, protein_data, diagnostics)

    # MODELLED ENTITY INSTANCES
    modelled_entity_instances = xml_tree.findall("ModelledEntityInstance")
    process_modelled_entity_instances(modelled_entity_instances, protein_data, diagnostics)

    return protein_data, diagnostics


def process_modelled_subgroups(
        modelled_subgroups: list[Element],
        ligand_infos: dict[str, LigandInfo],
        data: ProteinDataFromXML,
        diagnostics: Diagnostics
):
    ligand_count = 0
    ligand_count_10_and_below = 0
    ligand_count_11_and_above = 0
    residue_count = 0

    ligand_rsr_sum = 0.0
    has_ligand_rsr = False
    residue_rsr_sum = 0.0
    has_residue_rsr = False
    ligand_rscc_sum = 0.0
    ligand_rscc_outlier_count = 0
    has_ligand_rscc = False
    ligand_rscc_sum_10_and_below = 0.0
    ligand_rscc_sum_11_and_above = 0.0
    has_ligand_rscc_sum_10_and_below = False
    has_ligand_rscc_sum_11_and_above = False
    residue_rscc_sum = 0.0
    residue_rscc_outlier_count = 0
    has_residue_rscc = False
    ligand_rmsz_sum_angles = 0.0
    ligand_rmsz_sum_bonds = 0.0
    has_ligand_rmsz_angles = False

    for element in modelled_subgroups:
        if "mogul_bonds_rmsz" in element.attrib:  # it is ligand
            # START OF LIGAND TODO REFACTOR
            ligand_count += 1
            mogul_bonds_rmsz = to_float(element.get("mogul_bonds_rmsz"))
            if mogul_bonds_rmsz:
                ligand_rmsz_sum_bonds += mogul_bonds_rmsz
            else:
                record_extraction_error(diagnostics, element, "mogul_bonds_rmsz")

            if "mogul_angles_rmsz" in element.attrib:
                mogul_angles_rmsz = to_float(element.get("mogul_angles_rmsz"))
                if mogul_angles_rmsz:
                    has_ligand_rmsz_angles = True
                    ligand_rmsz_sum_angles += mogul_angles_rmsz
                else:
                    record_extraction_error(diagnostics, element, "mogul_angles_rmsz")

            if "rsr" in element.attrib:
                rsr = to_float(element.get("rsr"))
                if rsr:
                    has_ligand_rsr = True
                    ligand_rsr_sum += rsr
                else:
                    record_extraction_error(diagnostics, element, "rsr")

            rscc = None  # also needed later with ligand info
            if "rscc" in element.attrib:
                rscc = to_float(element.get("rscc"))
                if rscc:
                    has_ligand_rscc = True
                    ligand_rscc_sum += rscc
                    if rscc < 0.8:
                        ligand_rscc_outlier_count += 1
                else:
                    record_extraction_error(diagnostics, element, "rscc")

            ligand_id = element.get("resname")
            ligand_info = ligand_infos.get(ligand_id)
            if not ligand_id:
                diagnostics.add_issue(IssueType.DATA_ITEM_ERROR,
                                      "Element has no resname, even though it was determined to be ligand because "
                                      "of mogul_bonds_rmsz presence.")
            elif not ligand_info:
                diagnostics.add_issue(IssueType.DATA_ITEM_ERROR,
                                      f"Ligand with ID '{ligand_id}' was not found in ligand infos.")
            elif ligand_info.heavy_atom_count > 10:
                ligand_count_11_and_above += 1
                if rscc:
                    ligand_rscc_sum_11_and_above += rscc
                    has_ligand_rscc_sum_11_and_above = True
            else:
                ligand_count_10_and_below += 1
                if rscc:
                    ligand_rscc_sum_10_and_below += rscc
                    has_ligand_rscc_sum_10_and_below = True
            # END OF LIGAND TODO REFACTOR
        else:  # it is not ligand
            # START OF NOT LIGAND TODO REFACTOR
            residue_count += 1

            if "rsr" in element.attrib:
                rsr = to_float(element.get("rsr"))
                if rsr:
                    has_residue_rsr = True
                    residue_rsr_sum += rsr
                else:
                    record_extraction_error(diagnostics, element, "rsr")

            if "rscc" in element.attrib:
                rscc = to_float(element.get("rscc"))
                if rscc:
                    has_residue_rscc = True
                    residue_rscc_sum += rscc
                    if rscc < 0.8:
                        residue_rscc_outlier_count += 1
                else:
                    record_extraction_error(diagnostics, element, "rscc")
            # END OF LIGAND TODO REFACTOR

    # LOOP ENDED
    if residue_count > 0:
        if has_residue_rsr:
            data.average_residue_RSR = residue_rsr_sum / residue_count
        if has_residue_rscc:
            data.average_residue_RSCC = residue_rscc_sum / residue_count
            data.residue_RSCC_outlier_ratio = residue_rscc_outlier_count / residue_count

    if ligand_count > 0:
        data.average_ligand_bond_RMSZ = ligand_rmsz_sum_bonds / ligand_count
        if has_ligand_rsr:
            data.average_ligand_RSR = ligand_rsr_sum / ligand_count
        if has_ligand_rscc:
            data.average_ligand_RSCC = ligand_rscc_sum / ligand_count
            data.ligand_RSCC_outlier_ratio = ligand_rscc_outlier_count / ligand_count
        if has_ligand_rmsz_angles:
            data.average_ligand_angle_RMSZ = ligand_rmsz_sum_angles / ligand_count

    if ligand_count_10_and_below > 0 and has_ligand_rscc_sum_10_and_below:
        data.average_ligand_RSCC_small_ligands = ligand_rscc_sum_10_and_below / ligand_count_10_and_below

    if ligand_count_11_and_above > 0 and has_ligand_rscc_sum_11_and_above:
        data.average_ligand_RSCC_large_ligands = ligand_rscc_sum_11_and_above / ligand_count_11_and_above


def process_modelled_entity_instances(
        modelled_entity_instances: list[Element],
        data: ProteinDataFromXML,
        diagnostics: Diagnostics
):
    for element in modelled_entity_instances:
        if "bonds_rmsz" in element.attrib:
            bonds_rmsz = to_float(element.get("bonds_rmsz"))
            if not bonds_rmsz:
                record_extraction_error(diagnostics, element, "bonds_rmsz")
            elif data.highest_chain_bonds_RMSZ is None or bonds_rmsz > data.highest_chain_bonds_RMSZ:
                data.highest_chain_bonds_RMSZ = bonds_rmsz

        if "angles_rmsz" in element.attrib:
            angles_rmsz = to_float(element.get("angles_rmsz"))
            if not angles_rmsz:
                record_extraction_error(diagnostics, element, "angles_rmsz")
            elif data.highest_chain_angles_RMSZ is None or angles_rmsz > data.highest_chain_angles_RMSZ:
                data.highest_chain_angles_RMSZ = angles_rmsz


def record_extraction_error(diagnostics: Diagnostics, element: Element, attribute_name: str):
    diagnostics.add_issue(IssueType.DATA_ITEM_ERROR,
                          f"Attribue {attribute_name} failed to convert to float. "
                          f"Value: '{element.get(attribute_name)}'")
