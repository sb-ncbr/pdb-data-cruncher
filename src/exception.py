class ParsingError(Exception):
    """
    Exception raised when custom processing of external files into internal representation encounters
    recoverable error.
    """


class RestParsingError(ParsingError):
    """
    Exception raised when processing of external files from REST apis encounters error.
    """


class DataDownloadError(Exception):
    """
    Exception raised when custom download of files fails.
    """
