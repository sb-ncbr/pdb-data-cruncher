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
        return default
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
        return default
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


def to_bool(value_to_convert: Any, default: Optional[bool] = None) -> Optional[bool]:
    """
    Safe way to convert to bool. If the conversion fails due to ValueError or TypeError, returns default value
    instead. Takes string case insensitively, off/on and 0/1.
    :param value_to_convert: String to be converted to bool.
    :param default: Value to return when conversion fails (None by default).
    :return: Converted bool, or default value.
    """
    if value_to_convert is None:
        return default
    if isinstance(value_to_convert, bool):
        return value_to_convert

    if value_to_convert in ["true", "TRUE", "True", "on", "1", 1]:
        return True
    if value_to_convert in ["false", "FALSE", "False", "off", "0", 0]:
        return False
    return default


def to_int_or_float(value_to_convert: str, default: Union[float, int, None] = None) -> Union[float, int, None]:
    """
    Safe way to convert to int or float, when unsure which type it is. If the conversion fails due to ValueError
    or TypeError, returns default value instead.
    :param value_to_convert: String to be converted to int or float.
    :param default: Value to return when conversion fails.
    :return: Converted int, if it is int, float if number that's not finite integer, default value otherwise.
    """
    float_value = to_float(value_to_convert)
    if float_value is None:
        return default
    if float_value.is_integer():
        int_value = to_int(value_to_convert)
        if int_value is not None:
            return int_value
    return float_value


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
