import logging
import argparse
import os

from src.exception import ParsingError
from src.config import Config, RunModeType
from src.data_parsers.ligand_stats_parser import parse_ligand_stats
from src.data_parsers.rest_parser import parse_rest
from src.data_loaders.json_file_loader import load_json_file


def parse_arguments_and_update_config(config: Config) -> None:
    """
    Parses arguments from commandline and updates the default values in config.

    :param config: Object holding program configuration.
    :return:
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

    config.logging_debug = args.logging_debug


def create_config_from_parsed_arguments() -> Config:
    """
    Creates config and updates it with any values passed via commandline.

    :return: Config loaded with updated values.
    """
    config = Config()
    parse_arguments_and_update_config(config)
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

    if not os.path.exists(config.temporary_files_folder_path):
        os.mkdir(config.temporary_files_folder_path)
        logging.info("Created folder %s for temporary files.", config.temporary_files_folder_path)

    # TODO only temporary endpoint for testing
    if config.run_mode == RunModeType.TEST:
        run_current_test(config)

    logging.debug("App finished running successfully")


# TODO setup logging into two seperate files like this (one errors or warnings only, second all)
# # Create the root logger
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)  # Set the root logger level to the lowest level you want to capture
#
# # Create a handler for errors_only.txt with a filter for ERROR level
# error_handler = logging.FileHandler('errors_only.txt')
# error_handler.setLevel(logging.ERROR)
# error_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
# error_handler.addFilter(lambda record: record.levelno == logging.ERROR)
#
# # Create a handler for all_errors.txt
# all_errors_handler = logging.FileHandler('all_errors.txt')
# all_errors_handler.setLevel(logging.DEBUG)
# all_errors_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
#
# # Add both handlers to the root logger
# root_logger.addHandler(error_handler)
# root_logger.addHandler(all_errors_handler)
#
# # Example usage
# logging.error("This message will be logged to errors_only.txt and all_errors.txt")
# logging.warning("This message will only be logged to all_errors.txt")
# logging.info("This message will only be logged to all_errors.txt")


def run_current_test(config: Config):
    try:
        protein_summary_json = load_json_file("./temp/8jip_summary.json")
        protein_assembly_json = load_json_file("./temp/8jip_assembly.json")
        protein_molecules_json = load_json_file("./temp/8jip_molecules.json")
    except ParsingError as ex:
        logging.error(f"Cannot parse file. Reason: {ex}")
        exit(1)

    ligand_information = parse_ligand_stats("./temp/ligandStats.csv")
    parse_rest("8jip",
               protein_summary_json,
               protein_assembly_json,
               protein_molecules_json,
               ligand_information)


if __name__ == "__main__":
    main()
