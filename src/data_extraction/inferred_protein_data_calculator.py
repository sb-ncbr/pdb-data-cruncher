from statistics import harmonic_mean

from src.models import ProteinDataComplete, ProteinDataInferred


def calculate_inferred_protein_data(data: ProteinDataComplete) -> None:
    """
    Calculates protein data that need multiple sources.
    :param data: All the collected protein data so far.
    """
    data.inferred = ProteinDataInferred()

    if data.vdb.ligand_count_filtered is not None:
        data.inferred.aa_ligand_count_filtered = data.vdb.ligand_count_filtered + data.pdbx.aa_count

    if data.xml is None:
        return  # There was no XML validation file for this protein

    clashscore_perc = data.xml.absolute_percentile_clashscore
    rama_perc = data.xml.absolute_percentile_percent_rama_outliers
    sidechain_perc = data.xml.absolute_percentile_percent_rota_outliers
    rna_perc = data.xml.absolute_percentile_rna_suiteness

    if clashscore_perc is not None and rama_perc is not None and sidechain_perc is not None:
        values_for_harmonic_mean = [clashscore_perc, rama_perc, sidechain_perc]
        if rna_perc is not None:
            values_for_harmonic_mean.append(rna_perc)
        data.inferred.combined_geometry_quality = harmonic_mean(values_for_harmonic_mean)

    r_free_perc = data.xml.absolute_percentile_dcc_r_free
    rsrz_perc = data.xml.absolute_percentile_percent_rsrz_outliers

    if r_free_perc is not None and rsrz_perc is not None:
        data.inferred.combined_x_ray_quality_metric = harmonic_mean([r_free_perc, rsrz_perc])

    if (
        data.inferred.combined_x_ray_quality_metric is not None
        and data.inferred.combined_geometry_quality is not None
        and data.pdbx.resolution is not None
    ):
        data.inferred.combined_overall_quality_metric = (
            data.inferred.combined_x_ray_quality_metric
            + data.inferred.combined_geometry_quality
            - 30.0 * data.pdbx.resolution
        ) / 2
