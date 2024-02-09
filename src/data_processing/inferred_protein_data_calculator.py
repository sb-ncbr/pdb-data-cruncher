from src.models import ProteinDataComplete, ProteinDataInferred


def calculate_inferred_protein_data(data: ProteinDataComplete) -> None:
    data.inferred = ProteinDataInferred()
    # TODO check for none values
    data.inferred.aa_ligand_count = data.pdbx.ligand_count + data.pdbx.aa_count
    data.inferred.aa_ligand_count_no_water = data.pdbx.ligand_count_no_water + data.pdbx.aa_count
    data.inferred.aa_ligand_count_filtered = data.vdb.ligand_count_filtered + data.pdbx.aa_count

    # TODO combined qulity metrics, but need another values for that
