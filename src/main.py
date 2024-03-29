import logging
import os.path
import sys

from src.data_transformation.data_transform_manager import run_data_transformation
from src.data_extraction.parsing_manger import run_data_extraction
from src.data_archivation.data_archivation_manager import run_data_archivation
from src.data_download.data_download_manager import run_data_download
from src.config import Config


def prepare_log_folder(config: Config) -> None:
    """
    Ensures log folder exists, discards old logs and renames the last logs with prefix "previous".
    :param config: Application configuraiton.
    """
    if not os.path.exists(config.filepaths.logs_root_path):
        os.mkdir(config.filepaths.logs_root_path)
    else:
        if os.path.exists(config.filepaths.previous_filtered_log):
            os.remove(config.filepaths.previous_filtered_log)
        if os.path.exists(config.filepaths.previous_full_log):
            os.remove(config.filepaths.previous_full_log)
        if os.path.exists(config.filepaths.filtered_log):
            os.rename(config.filepaths.filtered_log, config.filepaths.previous_filtered_log)
        if os.path.exists(config.filepaths.full_log):
            os.rename(config.filepaths.full_log, config.filepaths.previous_full_log)


def configure_logging(config: Config) -> None:
    """
    Configures logging based on configuration - two file logs and one std log stream.
    :param config: Application configuration.
    """
    logging_level = logging.DEBUG if config.logging_debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(logging_level)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s (%(filename)s:%(lineno)d)")

    # logging to file in full
    full_log_file_handler = logging.FileHandler(config.filepaths.full_log)
    full_log_file_handler.setFormatter(formatter)

    # logging to file filtering info/debug out
    filtered_log_file_handler = logging.FileHandler(config.filepaths.filtered_log)
    filtered_log_file_handler.setFormatter(formatter)
    filtered_log_file_handler.setLevel(logging.WARNING)

    # logging to the stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(full_log_file_handler)
    root_logger.addHandler(filtered_log_file_handler)
    root_logger.addHandler(stream_handler)

    logging.info("Logging set up to '%s' and '%s' files.", config.filepaths.full_log, config.filepaths.filtered_log)
    logging.debug("Starting pdb-data-cruncher app with following configuration: %s", config)


def run_app(config: Config) -> None:
    """
    Run the app.
    :param config:
    """
    if config.run_data_download_only:
        if not run_data_download(config):
            sys.exit("Data download failed.")
    elif config.run_data_extraction_only:
        if not run_data_extraction(config):
            sys.exit("Data extraction failed.")
    elif config.run_zipping_files_only:
        if not run_data_archivation(config):
            sys.exit("Data archivation failed.")
    elif config.run_data_transformation_only:
        if not run_data_transformation(config):
            sys.exit("Data transformation failed.")
    else:
        run_app_full_flow(config)


def run_app_full_flow(config):
    """
    Run the full run of the app (download -> archiving -> extraction -> transformation). If download or extraction
    fails, the rest is not done. The app exits with error code after any of the parts failure.
    :param config:
    """
    if not run_data_download(config):
        sys.exit("Cannot continue because data download failed.")
    archivation_success = run_data_archivation(config)
    if not run_data_extraction(config):
        sys.exit("Cannot continue because data extraction failed.")
    transformation_success = run_data_transformation(config)
    if not archivation_success or not transformation_success:
        sys.exit(
            f"{'Data archivation failed. ' if not archivation_success else ''}"
            f"{'Data transformation failed.' if not transformation_success else ''}"
        )


def main():
    """
    Application entrypoint.
    """
    config = Config()
    config.validate()
    prepare_log_folder(config)
    configure_logging(config)
    run_app(config)
    logging.info("App finished running.")


# def run_current_test(config: Config):
#     """
#     Temporary testing function.
#     :param config: App config.
#     """
#     pdb_ids = ["1dey", "1htq", "1i4c", "1vcr", "2dh1", "2pde", "2qz5", "3p4a", "3rec",
#                "3zpm", "4v4a", "4v43", "5dh6", "5j7v", "5qej", "5tga", "5zck", "6dwu",
#                "7as5", "7pin", "7y7a", "8ckb", "8ucv", "103d"]
#     run_full_data_extraction(pdb_ids, config)
#
#
# def run_full_data_extraction(pdb_ids: list[str], config: Config):
#     """
#     Collect all protein data from given protein IDs, run multithreaded. After the collection,
#     output the collected data into crunched csv.
#     :param pdb_ids: Ids to extract data from.
#     :param config: App config containing max threads and paths to files from which the data is extracted.
#     :return:
#     """
#     start_time = time.monotonic()
#     ligand_stats = ParsingManger.load_and_parse_ligand_stats(config)
#     with Pool(config.max_process_count_in_multiprocessing) as p:
#         collected_data = p.starmap(
#             ParsingManger.load_all_protein_data, [(pdb_id, config, ligand_stats) for pdb_id in pdb_ids]
#         )
#     ParsingManger.store_protein_data_into_crunched_csv(collected_data, config)
#     end_time = time.monotonic()
#     logging.info("Full data extraction completed in %s.", timedelta(seconds=end_time - start_time))
#
#
# def run_create_all(config: Config):
#     if not os.path.exists(config.output_root_path):
#         os.mkdir(config.output_root_path)
#
#     config.crunched_data_csv_path = "../output/20240314_crunched.csv"
#
#     # DataTransformManager.create_default_plot_data(config)
#     # DataTransformManager.create_distribution_data(config)
#     DataTransformManager.create_default_plot_settings(config)
#     DataTransformManager.create_updated_factor_hierarchy(config)
#     DataTransformManager.create_updated_versions_jsons(config)
#
#     logging.info("Phase of creating all neccessary output data has finished.")


if __name__ == "__main__":
    main()
