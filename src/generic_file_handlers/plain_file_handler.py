import logging

from src.exception import ParsingError, FileWritingError


def load_text_file_as_lines(filepath: str) -> list[str]:
    """
    Read file contents and return them as (stripped of whitespace on the start and end) lines.
    :param filepath: Path to the file.
    :return: List of strings.
    """
    try:
        with open(filepath, "r", encoding="utf8") as f:
            return [line.strip() for line in f.readlines()]
    except OSError as ex:
        raise ParsingError(f"Failed to read and split into lines file {filepath}: {ex}") from ex


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
