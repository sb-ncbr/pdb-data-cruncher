from src.models import ProteinDataComplete, ProteinDataInferred, Diagnostics


def calculate_inferred_protein_data(data: ProteinDataComplete) -> None:
    data.inferred = ProteinDataInferred()

    data.inferred.aa_ligand_count = data.pdbx.ligand_count + data.pdbx.aa_count
    data.inferred.aa_ligand_count_no_water = data.pdbx.ligand_count_no_water + data.pdbx.aa_count
    if data.vdb.ligand_count_filtered is not None:
        data.inferred.aa_ligand_count_filtered = data.vdb.ligand_count_filtered + data.pdbx.aa_count

    clashscore_perc = data.xml.absolute_percentile_clashscore
    rama_perc = data.xml.absolute_percentile_percent_rama_outliers
    sidechain_perc = data.xml.absolute_percentile_percent_rota_outliers
    rna_perc = data.xml.absolute_percentile_rna_suiteness

    if clashscore_perc and rama_perc and sidechain_perc:  # if all are not None and not 0
        summation = 1.0 / clashscore_perc + 1.0 / rama_perc + 1.0 / sidechain_perc
        if rna_perc is not None:
            summation += 1.0 / rna_perc
        data.inferred.combined_geometry_quality = 1.0 / (summation / 3.0)

    r_free_perc = data.xml.absolute_percentile_dcc_r_free
    rsrz_perc = data.xml.absolute_percentile_percent_rsrz_outliers

    if r_free_perc and rsrz_perc:  # if all are not None and not 0
        summation = 1.0 / r_free_perc + 1.0 / rsrz_perc
        data.inferred.combined_x_ray_quality_metric = 1.0 / (summation / 2.0)

    if data.inferred.combined_x_ray_quality_metric is not None and data.inferred.combined_geometry_quality is not None and data.pdbx.resolution is not None:
        data.inferred.combined_overall_quality_metric = (
            data.inferred.combined_x_ray_quality_metric +
            data.inferred.combined_geometry_quality -
            30.0 * data.pdbx.resolution
        ) / 2
