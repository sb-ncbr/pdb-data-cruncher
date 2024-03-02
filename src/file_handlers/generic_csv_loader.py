import logging
from typing import Optional, Generator
import csv

from src.exception import ParsingError


def csv_reader_generator(filepath: str, selected_column_names: Optional[list[str]]) -> Generator[list[str], None, None]:
    selected_column_indices = None
    try:
        with open(filepath, encoding="utf8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")

            header = next(csv_reader)
            if selected_column_names:
                selected_column_indices = [i for i, name in enumerate(header) if name in selected_column_names]

            for row in csv_reader:
                if selected_column_indices:
                    sliced_row = _get_only_wanted_columns(row, selected_column_indices)
                    if sliced_row is None:
                        continue
                    else:
                        yield sliced_row
                else:
                    yield row
    except OSError as ex:
        raise ParsingError(f"CSV {filepath} cannot be read or parsed") from ex


def _get_only_wanted_columns(row: list[str], selected_column_indices: list[int]) -> Optional[list[str]]:
    if len(row) <= max(selected_column_indices):
        logging.warning(
            "Failed to extract row because it had less items than needed with the selected column"
            "indices. Row: %s, selected column indices: %s. Row is skipped.",
            row,
            selected_column_indices
        )
        return None

    return [row[index] for index in selected_column_indices]
