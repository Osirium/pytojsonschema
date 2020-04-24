import ast
import copy
import typing

BASE_SCHEMA_MAP = {
    "bool": {"type": "boolean"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "str": {"type": "string"},
}
VALID_TYPING_AST_SUBSCRIPT_TYPES = frozenset({"Union", "List", "Dict", "Optional"})
VALID_TYPING_TYPES = VALID_TYPING_AST_SUBSCRIPT_TYPES | frozenset({"TypedDict", "Any"})
VALID_ENUM_TYPES = frozenset({"Enum"})
VALID_TYPES = VALID_TYPING_TYPES | VALID_ENUM_TYPES

TypeNamespace = typing.Dict[str, typing.Set[str]]
Schema = typing.Dict[str, typing.Any]
SchemaMap = typing.Dict[str, Schema]


class InvalidTypeAnnotation(Exception):
    pass


def init_typing_namespace() -> TypeNamespace:
    """
    Initialize the typing namespace, whose keys are the supported typing types and the values how we can use them.
    Initial values are empty sets for all the typing types we support (keys)

    :return: A TypeNamespace object
    """
    return {valid_type: set() for valid_type in VALID_TYPES}


def init_schema_map() -> SchemaMap:
    """
    Initialize the schema map, a dictionary containing the types that translate to a concrete json schema.
    Initial values are the schemas for the bool, int, float, str and None types (keys).

    :return: A SchemaMap object
    """
    return copy.deepcopy(BASE_SCHEMA_MAP)


def get_ast_name_or_attribute_string(ast_element: typing.Union[ast.Name, ast.Attribute]) -> str:
    """
    Get the string representation of an ast name or ast attribute element.

    :param ast_element: An ast name or ast attribute element
    :return: A string
    """
    if isinstance(ast_element, ast.Name):
        return ast_element.id
    elif isinstance(ast_element.value, ast.Name):
        return f"{ast_element.value.id}.{ast_element.attr}"
    else:
        return f"{get_ast_name_or_attribute_string(ast_element.value)}.{ast_element.attr}"
