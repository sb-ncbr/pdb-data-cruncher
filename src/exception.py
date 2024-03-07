class ParsingError(Exception):
    """
    Exception raised when custom processing of external files into internal representation encounters
    error that prevents further parsing of file in question.
    """


class RestParsingError(ParsingError):
    """
    Exception raised when processing of external files from REST apis encounters error.
    """


class PDBxParsingError(ParsingError):
    """
    Exception raised when processing of external files in PDBx format encounters an error.
    """


class DataDownloadError(Exception):
    """
    Exception raised when custom download of files fails.
    """


class DataTransformationError(Exception):
    """
    Exception raised when transforming data into needed output files fails.
    """


class FileWritingError(Exception):
    """
    Exception raised when encountering error while trying to write content into file.
    """


class IrrecoverableError(Exception):
    """
    Exception raised when encountering such severe issues that the program cannot continue.
    """


class CrunchedCsvAssemblyError(IrrecoverableError):
    """
    Exception raised when creation of crunched csv fails.
    """
