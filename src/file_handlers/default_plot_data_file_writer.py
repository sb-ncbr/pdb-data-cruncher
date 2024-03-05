import logging

from src.models.transformed import DefaultPlotData
import os


def write_default_plot_data_into_zip(default_plot_data: list[DefaultPlotData], location_filepath: str) -> None:
    # TODO should be different
    from src.file_handlers.json_file_writer import write_json_file
    plot_data_dir = os.path.join(location_filepath, "plot_data_test")
    if not os.path.exists(plot_data_dir):
        os.mkdir(plot_data_dir)
    for plot_data in default_plot_data:
        filepath = os.path.join(plot_data_dir, f"{plot_data.x_factor.value}+{plot_data.y_factor.value}.json")
        write_json_file(filepath, plot_data.to_dict())
    logging.info("Default plot data writen")
