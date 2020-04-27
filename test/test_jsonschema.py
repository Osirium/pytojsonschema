import ast
import functools

import pytest

from pytojsonschema.common import init_schema_map, InvalidTypeAnnotation
from pytojsonschema.jsonschema import get_json_schema_from_ast_element
from pytojsonschema.types import ANY_SCHEMA

from .conftest import assert_expected, TEST_TYPING_NAMESPACE


@pytest.mark.parametrize(
    "ast_element, type_namespace, schema_map, expected",
    [
        [ast.parse("None").body[0].value, TEST_TYPING_NAMESPACE, init_schema_map(), {"type": "null"}],
        [ast.parse("bool").body[0].value, TEST_TYPING_NAMESPACE, init_schema_map(), {"type": "boolean"}],
        [
            ast.parse("complex").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation(
                "Type 'complex' is invalid. Base types and the ones you have imported are bool, int, float, str. "
                "Did you miss an import?"
            ),
        ],
        [
            ast.parse("Union[str, int]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation(
                "Type 'Union' is invalid. You have imported typing.Dict, typing.List, typing.Optional, "
                "typing.Union, and we allow Dict, List, Optional, Union. Did you miss an import?"
            ),
        ],
        [
            ast.parse("typing.Union[str, int]").body[0].value,
            {},
            init_schema_map(),
            InvalidTypeAnnotation(
                "Type 'typing.Union' is invalid, but no valid types were found. Did you forget importing typing?"
            ),
        ],
        [
            ast.parse("typing.List[str]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {"type": "array", "items": {"type": "string"}},
        ],
        [
            ast.parse("typing.Optional[int]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        ],
        [
            ast.parse("typing.Optional[typing.Any]").body[0].value,
            TEST_TYPING_NAMESPACE,
            dict(init_schema_map(), **{"typing.Any": ANY_SCHEMA}),
            {"anyOf": [ANY_SCHEMA, {"type": "null"}]},
        ],
        [
            ast.parse("typing.Union[str]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("Union cannot have a single element"),
        ],
        [
            ast.parse("typing.Dict[int, str]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("typing.Dict keys must be strings"),
        ],
        [
            ast.parse("typing.Dict[str, int]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {"type": "object", "additionalProperties": {"type": "integer"}},
        ],
        [
            ast.parse("typing.Union[int, str]").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {"anyOf": [{"type": "integer"}, {"type": "string"}]},
        ],
        [
            ast.parse("eval(35)").body[0].value,
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("Unknown type annotation ast element '<class '_ast.Call'>'"),
        ],
    ],
    ids=[
        "null",
        "base",
        "base_not_found",
        "subscript_missing_import",
        "subscript_missing_typing",
        "list",
        "optional",
        "optional_any",
        "bad_union",
        "dict_bad_keys",
        "dict",
        "union",
        "unsupported",
    ],
)
def test_get_json_schema_from_ast_element(ast_element, type_namespace, schema_map, expected):
    assert_expected(
        functools.partial(get_json_schema_from_ast_element, ast_element, type_namespace, schema_map), expected
    )
