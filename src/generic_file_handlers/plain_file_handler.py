import logging

from src.exception import FileWritingError, ParsingError


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


def load_file(filepath: str) -> str:
    """
    Load content from given filepath.
    :param filepath:
    :return: String representation of file content.
    """
    try:
        with open(filepath, "r", encoding="utf8") as f:
            return f.read()
    except OSError as ex:
        raise ParsingError(f"Failed to read file {filepath}: {ex}") from ex
