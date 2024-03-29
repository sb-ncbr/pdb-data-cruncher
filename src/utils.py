import decimal
import logging
import math
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any, get_type_hints, Union, get_args

from src.models import FactorType


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


def int_from_env(env_variable_name: str, default_value: Optional[int] = None) -> Optional[int]:
    """
    Attempts to get value from environment variable, and converts it to int.
    :param env_variable_name: Name of the environment variable to find.
    :param default_value:
    :return: Converted environmental variable, or default.
    """
    return to_int(os.environ.get(env_variable_name), default_value)


def float_from_env(env_variable_name: str, default_value: Optional[float] = None) -> Optional[float]:
    """
    Attempts to get value from environment variable, and converts it to float.
    :param env_variable_name: Name of the environment variable to find.
    :param default_value:
    :return: Converted environmental variable, or default.
    """
    return to_float(os.environ.get(env_variable_name), default_value)


def int_list_from_env(env_variable_name: str, default_value: Optional[list[int]] = None) -> list[int]:
    """
    Get value of environmental variable and cut it by commas, and convert those into integers.
    :param env_variable_name:
    :param default_value:
    :return: List of integers.
    """
    if default_value is None:
        default_value = []

    env_value = os.environ.get(env_variable_name)
    if not env_value:
        return default_value

    int_list = []
    for value in env_value.replace(" ", "").split(","):
        if value:  # skip empty items if any
            int_list.append(to_int(value))

    if None in int_list:
        raise ValueError(
            f"One or multiple items in env {env_variable_name} with value '{env_value}' failed to convert to int."
            "Expected list of number convertable to int, separated by commas."
        )

    return int_list


def string_list_from_env(env_variable_name: str, default_value: Optional[list[str]] = None) -> list[str]:
    """
    Get value of environmental variable and cut it by commas, creating list of string values.
    :param env_variable_name:
    :param default_value:
    :return: List of strings.
    """
    if default_value is None:
        default_value = []

    env_value = os.environ.get(env_variable_name)
    if not env_value:
        return default_value

    string_list = []
    for value in env_value.replace(" ", "").split(","):
        if value:  # skip empty items if any
            string_list.append(value)

    return string_list


def bool_from_env(env_variable_name: str, default_value: bool) -> bool:
    """
    Attempts to get value from environment variable, and converts it to bool. Permitted values are
    (case-insensitive): true/on/1 for true, false/off/0 for false.
    :param env_variable_name: Name of the environment variable to find.
    :param default_value:
    :return: Converted environmental variable, or default.
    """
    env_value = os.environ.get(env_variable_name)
    if env_value is None:
        return default_value

    if env_value.lower() in ["true", "on", "1"]:
        return True
    if env_value.lower() in ["false", "off", "0"]:
        return False

    logging.warning(
        "Environmental variable %s (value %s) failed to convert to bool. Using default.", env_variable_name, env_value
    )
    return default_value


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


def get_factor_type(string_value: str) -> Optional[FactorType]:
    """
    Get FactorType with value as given string value. Returns None if none such exists.
    :param string_value: Value of the factor.
    :return: FactorType or None.
    """
    for factor_type in FactorType:
        if factor_type.value == string_value:
            return factor_type
    return None


def round_decimal_place_relative(number_to_round: Union[int, float], significant_decimal_places: int = 3) -> float:
    """
    Rounds given number to at most given amount of siginificant decimal places. If the number has a whole part,
    it is rounded in such a way so there are at most X decimal places minus digits in the whole part.
    E.g. in case of default value of 3 decimal places:\n
    12345 -> 12345\n
    1.2345 -> 1.23\n
    0.00012345 -> 0.000123
    :param number_to_round: Number to round
    :param significant_decimal_places: Number of significant decimal places to have included at most
    :return: Rounded number
    """
    if significant_decimal_places < 1:
        raise ValueError("Significant decimal places value needs to be at least 1.")

    if isinstance(number_to_round, int) or number_to_round.is_integer():  # has no decimal places at all
        return number_to_round

    if number_to_round > 100:  # has at least three significant decimal places in the whole part
        return round(number_to_round)

    round_to = math.ceil(-math.log10(abs(number_to_round))) + significant_decimal_places - 1
    return round(number_to_round, round_to)


def ceiling_relative(number_to_round: Decimal, precision: int) -> Decimal:
    """
    Round given number with method ROUND_CEILING to the given precision (number of significant digits that will be
    left).
    :param number_to_round:
    :param precision: Number of significant digits to round to. E.g. 1234 with precision 2 -> 1300
    :return: Rounded number.
    """
    return round_with_precision(number_to_round, precision, decimal.ROUND_CEILING)


def floor_relative(number_to_round: Decimal, precision: int) -> Decimal:
    """
    Round given number with method ROUND_FLOOR to the given precision (number of significant digits that will be
    left).
    :param number_to_round:
    :param precision: Number of significant digits to round to. E.g. 7890 with precision 2 -> 7800
    :return: Rounded number.
    """
    return round_with_precision(number_to_round, precision, decimal.ROUND_FLOOR)


def round_with_precision(number_to_round: Decimal, precision: int, rounding_method: Optional[str] = None) -> Decimal:
    """
    Round given number to the given precision (number of significant digits that will be
    left).
    :param number_to_round:
    :param precision: Number of significant digits to round to.
    :param rounding_method: String corresponding with one of decimal module supported values. Sets different method
    for rounding. If none is given, it rounds using default method in decimal module.
    :return: Rounded number.
    """
    with decimal.localcontext() as deciml_ctx:
        deciml_ctx.prec = precision
        if rounding_method is not None:
            deciml_ctx.rounding = rounding_method
        return +number_to_round  # need to do aritmetic operation for the precision constraint to apply


def get_formatted_date() -> str:
    """
    Get current date in the format %Y%m%d (e.g. 20240101)
    :return: The string with the date.
    """
    return datetime.now().strftime("%Y%m%d")


def find_matching_files(folder_path: str, string_to_match: str) -> list[str]:
    """
    Find files in given folder path that contain given string exactly.
    :param folder_path:
    :param string_to_match:
    :return: List of matched filenames (without full path).
    """
    all_filenames = next(os.walk(folder_path), (None, None, []))[2]  # [] if no file
    return [filename for filename in all_filenames if string_to_match in filename]


def find_matching_subfolders(folder_path: str, string_to_match: str) -> list[str]:
    """
    Find subfolders in given folder path that contain given string exactly.
    :param folder_path:
    :param string_to_match:
    :return: List of matched folder names (without full path).
    """
    all_filenames = next(os.walk(folder_path), (None, [], None))[1]  # [] if no subdirectories
    return [filename for filename in all_filenames if string_to_match in filename]
