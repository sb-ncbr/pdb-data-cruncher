import logging

from src.exception import FileWritingError


def write_file(filepath: str, content: str) -> None:
    """
    Write content into given filepath.
    :param filepath:
    :param content:
    :raise FileWritingError: On error with writing/saving file.
    """
    try:
        with open(filepath, "w", encoding="utf8") as f:
            f.write(content)
            logging.info("Saved file %s", filepath)
    except OSError as ex:
        raise FileWritingError(f"Failed to write file {filepath}: {ex}") from ex
