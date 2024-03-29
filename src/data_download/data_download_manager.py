from src.config import Config


def run_data_download(config: Config) -> bool:
    """
    Download new data and create files with changed pdb ids.
    :param config: Application configuration.
    :return: True if action succeeded. False otherwise.
    """
    raise NotImplementedError()
