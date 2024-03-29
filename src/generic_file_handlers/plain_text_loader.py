from src.exception import ParsingError


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
