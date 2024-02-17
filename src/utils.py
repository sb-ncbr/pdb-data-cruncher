from typing import Optional, Any, get_type_hints, Union, get_args


def to_float(value_to_convert: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safe way to convert to float. If the conversion fails due to ValueError or TypeError, returns default value
    instead. However, it does not catch OverflowError. Returns unchanged if the type already is float.
    :param value_to_convert: String to be converted to float.
    :param default: Value to return when conversion fails.
    :return: Converted float, or default value.
    """
    if value_to_convert is None:
        return None
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
    if value_to_convert is None:
        return None
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


def get_clean_type_hint(instance: object, field_name: str) -> Optional[type]:
    """
    Get the type hint for object's field.
    :param instance: Any object.
    :param field_name: Name of the object's field to inspect.
    :return: Type of the field, or None.
    """
    try:
        type_hint = get_type_hints(instance)[field_name]
        if type_hint.__origin__ == Union:  # Union in this code comes from Optional (given type, or None)
            return get_args(type_hint)[0]
        return type_hint
    except (IndexError, KeyError):
        return None
