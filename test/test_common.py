import ast

import pytest

from pytojsonschema.common import init_typing_namespace, init_schema_map, get_ast_name_or_attribute_string


def test_init_typing_namespace():
    assert init_typing_namespace() == {
        "Union": set(),
        "List": set(),
        "Dict": set(),
        "Optional": set(),
        "Any": set(),
        "TypedDict": set(),
        "Enum": set(),
    }


def test_init_schema_map():
    assert init_schema_map() == init_schema_map()


@pytest.mark.parametrize(
    "ast_element, expected",
    [
        [ast.parse("a").body[0].value, "a"],
        [ast.parse("a.b").body[0].value, "a.b"],
        [ast.parse("a.b.c").body[0].value, "a.b.c"],
        [ast.parse("a.b.c.d").body[0].value, "a.b.c.d"],
    ],
    ids=["single", "double", "triple", "quadruple"],
)
def test_get_ast_attribute_string(ast_element, expected):
    assert get_ast_name_or_attribute_string(ast_element) == expected
