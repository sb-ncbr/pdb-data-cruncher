from typing import Optional


def to_float(string_value: str, default: Optional[float] = None) -> Optional[float]:
    """
    Safe way to convert to float. If the conversion fails due to ValueError or TypeError, returns default value
    instead. However, it does not catch OverflowError.
    :param string_value: String to be converted to float.
    :param default: Value to return when conversion fails.
    :return: Converted float, or default value.
    """
    try:
        return float(string_value)
    except (ValueError, TypeError):
        return default


def to_int(string_value: str, default: Optional[int] = None) -> Optional[int]:
    """
    Safe way to convert to int. If the conversion fails due to ValueError or TypeError, returns default value
    instead.
    :param string_value: String to be converted to int.
    :param default: Value to return when conversion fails.
    :return: Converted int, or default value.
    """
    try:
        return int(string_value)
    except (ValueError, TypeError):
        return default
