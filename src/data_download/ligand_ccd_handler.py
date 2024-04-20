import logging
import os
from dataclasses import dataclass
from typing import Generator

import requests

from src.exception import DataDownloadError, FileWritingError
from src.generic_file_handlers.plain_file_handler import write_file
from src.models.ids_to_update import ChangedIds
from src.utils import find_matching_files, compare_file_and_string


@dataclass
class OneLigandCifContent:
    ligand_id: str
    content: str


def download_and_find_changed_ligand_cifs(ligand_cifs_folder_path: str, download_timeout_s: int) -> ChangedIds:
    """
    Find changed ligand cif files. Delete or update the files for them, and return lists of those
    updated and deleted.
    :param ligand_cifs_folder_path:
    :param download_timeout_s:
    :return: Changed ids.
    """
    ligand_ids_present = {
        ligand_file.replace(".cif", ""): False
        for ligand_file
        in find_matching_files(ligand_cifs_folder_path, ".cif")
    }

    components_generator = _one_ligand_cif_from_request_generator(
        "https://files.wwpdb.org/pub/pdb/data/monomers/components.cif", download_timeout_s
    )
    aa_variants_generator = _one_ligand_cif_from_request_generator(
        "https://files.wwpdb.org/pub/pdb/data/monomers/aa-variants-v1.cif", download_timeout_s
    )

    changed_ids = ChangedIds()

    for generator in [components_generator, aa_variants_generator]:
        for cif_content in generator:
            _process_one_ligand_cif(cif_content, changed_ids, ligand_cifs_folder_path, ligand_ids_present)

    for ligand_id, present_in_downloaded in ligand_ids_present.items():
        if not present_in_downloaded:
            changed_ids.deleted.append(ligand_id)
            _delete_ligand_file(ligand_id, ligand_cifs_folder_path)

    return changed_ids


def _process_one_ligand_cif(
    cif_content: OneLigandCifContent,
    changed_ids: ChangedIds,
    ligand_cifs_folder_path: str,
    ligand_ids_present: dict[str, bool]
) -> None:
    try:
        if cif_content.ligand_id not in ligand_ids_present:
            _save_ligand_cif_into_file(cif_content, ligand_cifs_folder_path)
            changed_ids.updated.append(cif_content.ligand_id)
        else:
            if ligand_ids_present[cif_content.ligand_id]:
                return  # ligand was already processed from previous file source
            ligand_ids_present[cif_content.ligand_id] = True
            if not _downloaded_and_stored_ligand_cifs_identical(cif_content, ligand_cifs_folder_path):
                _save_ligand_cif_into_file(cif_content, ligand_cifs_folder_path)
                changed_ids.updated.append(cif_content.ligand_id)
    except (DataDownloadError, FileWritingError) as ex:
        logging.error(
            "Failed to determine if ligand %s needs to be updated and saved. Reason: %s",
            cif_content.ligand_id,
            ex
        )


def _one_ligand_cif_from_request_generator(
    address: str, download_timeout_s: int
) -> Generator[OneLigandCifContent, None, None]:
    response = requests.get(address, stream=True, timeout=download_timeout_s)
    if response.status_code != 200:
        raise DataDownloadError(f"Failed to download, request returned {response.status_code}. {response.content}")

    response_lines = response.iter_lines()
    one_ligand_lines = [bytes.decode(next(response_lines), "utf8")]
    logging.info("Connection to %s established, starting generating cif files.", address)
    for line in response_lines:
        line = bytes.decode(line, "utf8")
        if "data_" in line:
            yield _assemble_one_ligand_cif_content(one_ligand_lines)
            one_ligand_lines = []
        one_ligand_lines.append(line)

    yield _assemble_one_ligand_cif_content(one_ligand_lines)


def _assemble_one_ligand_cif_content(content_lines: list[str]) -> OneLigandCifContent:
    if len(content_lines[0]) < 6:
        raise DataDownloadError(
            "Unexpected chunk in all ligand ccd file download. Cannot proceed without header in form data_XXX."
            f"{content_lines}"
        )
    ligand_name = content_lines[0][5:]
    content_lines[-1] += os.linesep  # add newline at the end
    return OneLigandCifContent(
        ligand_id=ligand_name,
        content=os.linesep.join(content_lines)
    )


def _save_ligand_cif_into_file(cif_content, ligand_cifs_folder_path):
    filepath = os.path.join(ligand_cifs_folder_path, f"{cif_content.ligand_id}.cif")
    write_file(filepath, cif_content.content)


def _downloaded_and_stored_ligand_cifs_identical(cif_content, ligand_cifs_folder_path) -> bool:
    filepath = os.path.join(ligand_cifs_folder_path, f"{cif_content.ligand_id}.cif")
    return compare_file_and_string(filepath, cif_content.content)


def _delete_ligand_file(ligand_id, ligand_cifs_folder_path):
    filepath = os.path.join(ligand_cifs_folder_path, f"{ligand_id}.cif")
    os.remove(filepath)
    logging.info("Deleted file %s (because it was not in udpated ligands)", filepath)
