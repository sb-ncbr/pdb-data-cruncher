import logging

from src.config import Config
from src.data_loaders import load_ligand_stats


def main():
    """
    Application entrypoint.
    """
    config = Config()
    logging_level = logging.DEBUG if config.logging_debug else logging.INFO
    logging.basicConfig(level=logging_level,
                        format="%(asctime)s %(levelname)s: %(message)s")
    logging.debug("Starting mulsan app with following configuration: %s", config)
    load_ligand_stats(config.path_to_ligand_stats_csv)


if __name__ == "__main__":
    main()
