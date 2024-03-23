import logging
import argparse
from multiprocessing import Pool
from datetime import timedelta
import time

from src.data_extraction.parsing_manger import ParsingManger
from src.data_transformation.data_transform_manager import DataTransformManager
from src.config import Config, RunModeType


def parse_arguments_into_config() -> Config:
    """
    Parses arguments from commandline and updates the default values in config.

    :return: Object holding program configuration.
    """
    parser = argparse.ArgumentParser(
        prog="valtrendsdb_dataprep",
        description="TODO"
    )

    parser.add_argument("-d", "--debug", action="store_true", dest="logging_debug",
                        help="Turning debug mode on will result in more information about the state of program being "
                             "logged.")

    # TODO options for program mode, location of files and more

    args = parser.parse_args()

    return Config(
        logging_debug=args.logging_debug
    )


def create_config_from_parsed_arguments() -> Config:
    """
    Creates config and updates it with any values passed via commandline.

    :return: Config loaded with updated values.
    """
    config = parse_arguments_into_config()
    return config


def configure_logging(config: Config):
    """
    Configures logging based on configuration.

    :param config: Application configuration
    :return:
    """
    logging_level = logging.DEBUG if config.logging_debug else logging.INFO
    logging.basicConfig(level=logging_level,
                        format="%(asctime)s %(levelname)s: %(message)s (%(filename)s:%(lineno)d)")
    logging.debug("Starting pdb-data-cruncher app with following configuration: %s", config)


def main():
    """
    Application entrypoint.
    """
    config = create_config_from_parsed_arguments()
    configure_logging(config)

    if config.run_mode == RunModeType.CREATE_ALL:
        run_create_all(config)

    # TODO only temporary endpoint for testing
    if config.run_mode == RunModeType.TEST:
        run_current_test(config)

    logging.debug("App finished running successfully")


def run_current_test(config: Config):
    """
    Temporary testing function.
    :param config: App config.
    """
    pdb_ids = ["1dey", "1htq", "1i4c", "1vcr", "2dh1", "2pde", "2qz5", "3p4a", "3rec",
               "3zpm", "4v4a", "4v43", "5dh6", "5j7v", "5qej", "5tga", "5zck", "6dwu",
               "7as5", "7pin", "7y7a", "8ckb", "8ucv", "103d"]
    run_full_data_extraction(pdb_ids, config)


def run_full_data_extraction(pdb_ids: list[str], config: Config):
    """
    Collect all protein data from given protein IDs, run multithreaded. After the collection,
    output the collected data into crunched csv.
    :param pdb_ids: Ids to extract data from.
    :param config: App config containing max threads and paths to files from which the data is extracted.
    :return:
    """
    start_time = time.monotonic()
    ligand_stats = ParsingManger.load_and_parse_ligand_stats(config)
    with Pool(config.data_extraction_max_threads) as p:
        collected_data = p.starmap(
            ParsingManger.load_all_protein_data, [(pdb_id, config, ligand_stats) for pdb_id in pdb_ids]
        )
    ParsingManger.store_protein_data_into_crunched_csv(collected_data, config)
    end_time = time.monotonic()
    logging.info("Full data extraction completed in %s.", timedelta(seconds=end_time - start_time))


def run_create_all(config: Config):
    # TODO remove later, rewriting the path to crunched for testing
    config.crunched_data_csv_path = "../dataset/20240314_crunched.csv"

    # DataTransformManager.create_default_plot_data(config)
    # DataTransformManager.create_distribution_data(config)
    # DataTransformManager.create_default_plot_settings(config)
    # DataTransformManager.create_updated_factor_hierarchy(config)
    DataTransformManager.create_updated_versions_jsons(config)
    # ...
    logging.info("Phase of creating all neccessary output data has finished.")


if __name__ == "__main__":
    main()
