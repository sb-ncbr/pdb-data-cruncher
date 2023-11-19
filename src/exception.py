class FileContentParsingError(Exception):
    """
    Exception raised when custom processing of external files into internal representation encounters
    recoverable error.
    """


class DataDownloadError(Exception):
    """
    Exception raised when custom download of files fails.
    """
