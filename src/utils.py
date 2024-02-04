from typing import Optional, Any


def to_float(value_to_convert: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safe way to convert to float. If the conversion fails due to ValueError or TypeError, returns default value
    instead. However, it does not catch OverflowError. Returns unchanged if the type already is float.
    :param value_to_convert: String to be converted to float.
    :param default: Value to return when conversion fails.
    :return: Converted float, or default value.
    """
    if isinstance(value_to_convert, float):
        return value_to_convert
    try:
        return float(value_to_convert)
    except (ValueError, TypeError):
        return default


def to_int(value_to_convert: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Safe way to convert to int. If the conversion fails due to ValueError or TypeError, returns default value
    instead. Deals with scientific notation too. Returns unchanged if the type already is int.
    :param value_to_convert: String to be converted to int.
    :param default: Value to return when conversion fails.
    :return: Converted int, or default value.
    """
    if isinstance(value_to_convert, int):
        return value_to_convert
    if "e" in value_to_convert:  # to handle scientific notation
        try:
            return int(float(value_to_convert))
        except (ValueError, TypeError):
            return default
    else:
        try:
            return int(value_to_convert)
        except (ValueError, TypeError):
            return default
