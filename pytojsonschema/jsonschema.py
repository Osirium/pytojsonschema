import ast
import typing
import platform

from packaging import version

from .common import (
    TypeNamespace,
    SchemaMap,
    Schema,
    get_ast_name_or_attribute_string,
    VALID_TYPING_AST_SUBSCRIPT_TYPES,
    InvalidTypeAnnotation,
)


PYTHON_VERSION = version.parse(platform.python_version())
PRE_3_10 = PYTHON_VERSION < version.Version("3.10.0")


def get_json_schema_from_ast_element(
    ast_element: typing.Union[ast.Name, ast.Constant, ast.Attribute, ast.Subscript],
    type_namespace: TypeNamespace,
    schema_map: SchemaMap,
) -> Schema:
    """
    Return the json schema from an type annotation ast object.

    :param ast_element: An ast name, constant, attribute or subscript element
    :param type_namespace: The current typing namespace to be read
    :param schema_map: The current schema map to be read
    :return: A dictionary with the json schema
    """

    def _get_or_raise(element_string: str) -> dict:
        if element_string not in schema_map:
            raise InvalidTypeAnnotation(
                f"Type '{element_string}' is invalid. Base types and the ones you have imported are "
                f"{', '.join(schema_map.keys())}. Did you miss an import?"
            )
        return schema_map[element_string]

    if isinstance(ast_element, ast.Constant) and ast_element.kind is None:
        return {"type": "null"}
    elif isinstance(ast_element, (ast.Name, ast.Attribute)):
        return _get_or_raise(get_ast_name_or_attribute_string(ast_element))
    elif isinstance(ast_element, ast.Subscript):  # typing.List, typing.Dict, typing.Union and typing.Optional
        subscript_string = get_ast_name_or_attribute_string(ast_element.value)
        subscript_type = None
        for key in VALID_TYPING_AST_SUBSCRIPT_TYPES:
            if subscript_string in type_namespace.get(key, {}):
                subscript_type = key
                break
        if subscript_type is None:
            imported_types = []
            for key in VALID_TYPING_AST_SUBSCRIPT_TYPES:
                for element in type_namespace.get(key, {}):
                    imported_types.append(element)
            if imported_types:
                error_msg = (
                    f"Type '{subscript_string}' is invalid. You have imported {', '.join(sorted(imported_types))}, and "
                    f"we allow {', '.join(sorted(list(VALID_TYPING_AST_SUBSCRIPT_TYPES)))}. Did you miss an import?"
                )
            else:
                error_msg = (
                    f"Type '{subscript_string}' is invalid, but no valid types were found. Did you forget importing "
                    f"typing?"
                )
            raise InvalidTypeAnnotation(error_msg)

        # In python 3.10 ast_element.slice.value has become ast_element.slice
        #
        # example slice: <ast.Tuple object at 0xffffa90aa590>
        # example ctx field value: <ast.Load object at 0xffffb546b0d0>
        # example elts field value: [<ast.Name object at 0xffffb50ae560>, <ast.Name object at 0xffffb50ae530>]
        slice_object = ast_element.slice.value if PRE_3_10 else ast_element.slice
        if isinstance(slice_object, (ast.Constant, ast.Name, ast.Attribute, ast.Subscript)):
            inner_schema = get_json_schema_from_ast_element(slice_object, type_namespace, schema_map)
            if subscript_type == "List":
                return {"type": "array", "items": inner_schema}
            elif subscript_type == "Optional":
                return {"anyOf": [inner_schema, {"type": "null"}]}
            else:
                raise InvalidTypeAnnotation(f"{subscript_type} cannot have a single element")
        else:  # ast.Tuple
            if subscript_type == "Dict":
                if not (isinstance(slice_object.elts[0], ast.Name) and slice_object.elts[0].id == "str"):
                    raise InvalidTypeAnnotation("typing.Dict keys must be strings")
                return {
                    "type": "object",
                    "additionalProperties": get_json_schema_from_ast_element(
                        slice_object.elts[1], type_namespace, schema_map
                    ),
                }
            else:  # Union
                return {
                    "anyOf": [
                        get_json_schema_from_ast_element(element, type_namespace, schema_map)
                        for element in slice_object.elts
                    ]
                }
    else:
        raise InvalidTypeAnnotation(f"Unknown type annotation ast element '{str(type(ast_element))}'")
