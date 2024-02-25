from src.models.transformed import DefaultPlotBucket, DefaultPlotData, FactorPair


def create_default_plot_data(
        crunched_csv_filepath: str,
        factor_pairs: list[FactorPair],
) -> list[DefaultPlotData]:

    # TODO not the correct obviously
    test_plot_data = DefaultPlotData(
        "aaCount",
        "averageLigandAngleRMSZ"
    )

    bucket = DefaultPlotBucket(1)
    bucket.structure_count = 886
    bucket.x_factor_from.value = 0
    bucket.x_factor_to.value = 12
    bucket.y_factor_average = 1.58
    bucket.y_factor_high_quartile = 1.96
    bucket.y_factor_low_quartile = 0.92
    bucket.y_factor_maximum = 10.4
    bucket.y_factor_median = 1.40
    bucket.y_factor_minimum = 0

    test_plot_data.graph_buckets.append(bucket)
    return [test_plot_data]
