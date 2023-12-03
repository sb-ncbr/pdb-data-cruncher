import logging
import argparse
import os

from src.config import Config, RunModeType
from src.data_loaders import load_ligand_stats
from src.data_download import get_and_store_json


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
                        format="%(asctime)s %(levelname)s: %(message)s")
    logging.debug("Starting mulsan app with following configuration: %s", config)


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
        # load_ligand_stats(config.path_to_ligand_stats_csv)
        get_and_store_json("https://www.ebi.ac.uk/pdbe/api/pdb/entry/summary/8a34",
                           os.path.join(config.temporary_files_folder_path, "8a34_summary.json"),
                           config.http_requests_timeout_s)

    logging.debug("App finished running successfully")


if __name__ == "__main__":
    main()
