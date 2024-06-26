import logging
import os.path
import sys

from src.data_transformation.data_transform_manager import run_data_transformation
from src.data_extraction.data_extraction_manager import run_data_extraction
from src.data_archivation.data_archivation_manager import run_data_archivation
from src.data_download.data_download_manager import run_data_download
from src.config import Config
from src.post_transformation_actions.post_transformation_actions_manager import run_post_transformation_actions


def prepare_log_folder(config: Config) -> None:
    """
    Ensures log folder exists, discards old logs and renames the last logs with prefix "previous".
    :param config: Application configuraiton.
    """
    if not os.path.exists(config.filepaths.logs_root_path):
        os.mkdir(config.filepaths.logs_root_path)
    else:
        if os.path.exists(config.filepaths.filtered_log):
            os.remove(config.filepaths.filtered_log)
        if os.path.exists(config.filepaths.full_log):
            os.remove(config.filepaths.full_log)

    if not os.path.exists(config.filepaths.archive_rsync_logs):
        os.mkdir(config.filepaths.archive_rsync_logs)
    if not os.path.exists(config.filepaths.archive_app_logs):
        os.mkdir(config.filepaths.archive_app_logs)


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

    # logging to a timestamped file archive in full
    archive_log_file_handler = logging.FileHandler(config.filepaths.archive_full_log)
    archive_log_file_handler.setFormatter(formatter)

    # logging to file filtering info/debug out
    filtered_log_file_handler = logging.FileHandler(config.filepaths.filtered_log)
    filtered_log_file_handler.setFormatter(formatter)
    filtered_log_file_handler.setLevel(logging.WARNING)

    # logging to the stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(full_log_file_handler)
    root_logger.addHandler(archive_log_file_handler)
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
    elif config.run_post_transformation_actions_only:
        if not run_post_transformation_actions(config):
            sys.exit("Post transformation actions failed.")
    else:
        run_app_full_flow(config)


def run_app_full_flow(config):
    """
    Run the full run of the app (download -> archiving -> extraction -> transformation). If download or extraction
    fails, the rest is not run. The app exits with error code after any of the parts failure.
    :param config:
    """
    if not config.skip_data_download:
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
    if not run_post_transformation_actions(config):
        sys.exit("Post transformation actions failed")


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


if __name__ == "__main__":
    main()
