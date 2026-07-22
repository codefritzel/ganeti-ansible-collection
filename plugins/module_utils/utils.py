from typing import Any, Dict


def dict_diff(
    dict1: Dict[str, Any], dict2: Dict[str, Any], ignore: list[str] = []
) -> Dict[str, Any]:
    result = {}
    for key, value in dict1.items():
        other_value = dict2.get(key)

        if key in ignore:
            continue

        if isinstance(value, dict) and isinstance(other_value, dict):
            nested_diff = dict_diff(value, other_value)

            if nested_diff:
                result[key] = nested_diff

        elif value and other_value and other_value != value:
            result[key] = value

    return result
