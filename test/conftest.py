import typing

import pytest

TEST_TYPING_NAMESPACE = {
    "Union": {"typing.Union"},
    "List": {"typing.List"},
    "Dict": {"typing.Dict"},
    "Optional": {"typing.Optional"},
    "Any": {"typing.Any"},
    "TypedDict": {"typing.TypedDict"},
}


def assert_expected(callback: typing.Callable, expected: typing.Any) -> typing.NoReturn:
    if isinstance(expected, Exception):
        with pytest.raises(expected.__class__) as exception:
            callback()
        assert str(exception.value) == expected.args[0]
    else:
        assert callback() == expected
