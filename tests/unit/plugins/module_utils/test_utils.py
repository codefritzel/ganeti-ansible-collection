import pytest

from plugins.module_utils.utils import dict_diff


@pytest.mark.parametrize(
    "dict1, dict2, expected",
    [
        # no changes
        ({"a": 1, "b": {"c": 2}}, {"a": 1, "b": {"c": 2}}, {}),
        # simple value changed
        ({"a": 1}, {"a": 2}, {"a": 1}),
        # nested value changed
        (
            {"a": {"b": 1, "c": 2}},
            {"a": {"b": 2, "c": 2}},
            {
                "a": {
                    "b": 1,
                }
            },
        ),
        # new nested key
        ({"a": {"b": 1}}, {"a": {"b": 1, "c": 2}}, {}),
        # list comparison
        ({"a": [1, 2]}, {"a": [1, 2, 3]}, {"a": [1, 2]}),
        # ignore deleted keys
        ({"a": 1, "b": 2}, {"a": 1}, {}),
        # multiple changes
        (
            {"a": 1, "b": {"c": 1}, "d": [1]},
            {"a": 2, "b": {"c": 2}, "d": [1, 2]},
            {"a": 1, "b": {"c": 1}, "d": [1]},
        ),
        # Ignore None
        ({"a": None}, {"b": None}, {}),
    ],
)
def test_diff_dict(dict1, dict2, expected):
    assert dict_diff(dict1, dict2) == expected
