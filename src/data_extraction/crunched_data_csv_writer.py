import logging
from csv import DictWriter

from src.models import CSV_ATTRIBUTE_ORDER
from src.exception import CrunchedCsvAssemblyError


def create_crunched_csv_file(data_rows: list[dict[str, str]], path_to_crunched_csv: str) -> None:
    """
    Takes given protein data as dictionaries and stores it into newly created crunched csv.
    :param data_rows: List of protein data in a form of dictionary where key is csv column name, and value is the
    value to be inserted.
    :param path_to_crunched_csv: Path (inc. filename itself) where the crunched csv should be stored.
    :raise CrunchedCsvAssemblyError: If the crunched csv could not be created.
    :return:
    """
    logging.debug(
        "Start of crunched csv creation into '%s'. Got %s protein data to store.", path_to_crunched_csv, len(data_rows)
    )

    try:
        with open(path_to_crunched_csv, "w", encoding="utf8") as csv_output_file:
            csv_writer = DictWriter(
                csv_output_file, delimiter=";", fieldnames=CSV_ATTRIBUTE_ORDER, extrasaction="ignore"
            )
            csv_writer.writeheader()
            for data_row in data_rows:
                csv_writer.writerow(data_row)
            logging.info("Protein data saved into crunched csv sucessfully. (filepath: '%s')", path_to_crunched_csv)
    except OSError as ex:
        logging.error(
            "Failed to open file '%s' for writing crunched csv. Reason: %s. Cannot proceed. "
            "See INFO level for crunched data that would have been printed.",
            path_to_crunched_csv,
            ex,
        )
        _log_data_rows_as_csv_string(data_rows)
        raise CrunchedCsvAssemblyError("Failed to open file for writing. Cannot create crunched csv.") from ex


def _log_data_rows_as_csv_string(data_rows: list[dict[str, str]]) -> None:
    rows = [";".join(CSV_ATTRIBUTE_ORDER)]
    for data_row in data_rows:
        row = [data_row.get(csv_attribute) for csv_attribute in CSV_ATTRIBUTE_ORDER]
        rows.append(";".join(row))
    rows_as_string = "\n".join(rows)
    logging.info("%s", rows_as_string)
