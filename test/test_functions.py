import ast
import functools
import os
import tempfile

import pytest

from pytojsonschema.common import init_schema_map, InvalidTypeAnnotation
from pytojsonschema.functions import filter_by_patterns, process_function_def, process_file, process_package

from .conftest import assert_expected, TEST_TYPING_NAMESPACE


@pytest.mark.parametrize(
    "ast_function_def, type_namespace, schema_map, expected",
    [
        [
            ast.parse("def foo(a, /): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("Function 'foo' contains positional only arguments"),
        ],
        [
            ast.parse("def foo(a, *args): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("Function 'foo' contains a variable number positional arguments i.e. *args"),
        ],
        [
            ast.parse("def foo(**bar): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("Function 'foo' is missing its **bar type annotation"),
        ],
        [
            ast.parse("def foo(**bar: int): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": {"type": "integer"},
            },
        ],
        [
            ast.parse("def foo(a): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            InvalidTypeAnnotation("Function 'foo' is missing type annotation for the parameter 'a'"),
        ],
        [
            ast.parse("def foo(a: int = 3): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"a": {"type": "integer"}},
                "required": [],
                "additionalProperties": False,
            },
        ],
        [
            ast.parse("def foo(a: int): pass").body[0],
            TEST_TYPING_NAMESPACE,
            init_schema_map(),
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"a": {"type": "integer"}},
                "required": ["a"],
                "additionalProperties": False,
            },
        ],
    ],
    ids=[
        "posonly_args",
        "args",
        "missing_kwargs_annotation",
        "valid_kwargs",
        "missing_arg",
        "arg_default",
        "arg_no_default",
    ],
)
def test_process_function_def(ast_function_def, type_namespace, schema_map, expected):
    assert_expected(functools.partial(process_function_def, ast_function_def, type_namespace, schema_map), expected)


@pytest.mark.parametrize(
    "name, include_patterns, exclude_patterns, expected",
    [
        ["foo", None, None, True],
        ["foo", ["bar*"], None, False],
        ["foo", ["foo*"], None, True],
        ["foo", None, ["bar*"], True],
        ["foo", None, ["foo*"], False],
        ["foo", ["foo*"], ["bar*"], True],
        ["foo", ["foo*"], ["foo*"], False],
    ],
    ids=[
        "no_patterns",
        "include_miss",
        "include_finds",
        "exclude_miss",
        "exclude_finds",
        "exclude_override_miss",
        "exclude_override_finds",
    ],
)
def test_filter_by_patterns(name, include_patterns, exclude_patterns, expected):
    assert filter_by_patterns(name, include_patterns, exclude_patterns) == expected


def test_process_file():
    with tempfile.NamedTemporaryFile("w") as f:
        f.write("import typing\n\n\ndef foo(a: int): pass\n\n\ndef bar(b: int): pass\n\n\neval(3)")
        f.flush()
        assert process_file(f.name, None, ["bar*"]) == {
            "foo": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"a": {"type": "integer"}},
                "required": ["a"],
                "additionalProperties": False,
            }
        }


def test_process_package():
    init_schema = {
        "example.version": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "additionalProperties": False,
            "properties": {},
            "required": [],
            "type": "object",
        },
        "example.config.dev.common.get_config": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "additionalProperties": False,
            "properties": {},
            "required": [],
            "type": "object",
        },
        "example.config.prod.common.get_config": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "additionalProperties": False,
            "properties": {},
            "required": [],
            "type": "object",
        },
    }
    expected = {
        "example.service.start": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "additionalProperties": False,
            "properties": {
                "service": {
                    "additionalProperties": False,
                    "properties": {
                        "address": {"type": "string"},
                        "config": {
                            "additionalProperties": {
                                "anyOf": [
                                    {"type": "object"},
                                    {"type": "array"},
                                    {"type": "null"},
                                    {"type": "string"},
                                    {"type": "boolean"},
                                    {"type": "integer"},
                                    {"type": "number"},
                                ]
                            },
                            "type": "object",
                        },
                        "debug": {"type": "boolean"},
                        "port": {"anyOf": [{"type": "integer"}, {"type": "number"}]},
                        "tags": {"items": {"type": "string"}, "type": "array"},
                    },
                    "required": ["address", "port", "config", "tags", "debug"],
                    "type": "object",
                }
            },
            "required": ["service"],
            "type": "object",
        },
        "example.service._secret": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "additionalProperties": False,
            "properties": {"secret": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
            "required": [],
            "type": "object",
        },
    }
    expected.update(init_schema)
    assert process_package(os.path.join("test", "example")) == expected
    assert process_package(os.path.join("test", "example"), exclude_patterns=["service*"]) == init_schema
    current_dir = os.getcwd()
    os.chdir("test")
    try:
        assert process_package("example") == expected
    finally:
        os.chdir(current_dir)
