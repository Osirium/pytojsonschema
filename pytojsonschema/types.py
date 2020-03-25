import ast
import logging
import os
import typing

from .common import (
    TypingNamespace,
    SchemaMap,
    get_ast_name_or_attribute_string,
    init_schema_map,
    init_typing_namespace,
    VALID_AST_SUBSCRIPTS,
    VALID_TYPES,
)
from .jsonschema import get_json_schema_from_ast_element

ANY_SCHEMA = {
    "anyOf": [
        {"type": "object"},
        {"type": "array"},
        {"type": "null"},
        {"type": "string"},
        {"type": "boolean"},
        {"type": "integer"},
        {"type": "number"},
    ]
}

LOGGER = logging.getLogger()


def process_alias(ast_alias: ast.alias) -> str:
    """
    Process an ast alias to return its alias or its name, if alias is not present.

    :param ast_alias: An ast alias object
    :return: A string with the resolved name
    """
    if ast_alias.asname is None:
        return ast_alias.name
    else:
        return ast_alias.asname


def process_import(ast_import: ast.Import, typing_namespace: TypingNamespace, schema_map: SchemaMap) -> typing.NoReturn:
    """
    This function accomplishes two things:
    - Process a normal import to add typing or a typing alias to the typing namespace
    - Given the case above, add the typing.Any (Or typing_alias.Any) schema to the list of valid schemas

    :param ast_import: An ast import object
    :param typing_namespace: The current typing namespace to be updated
    :param schema_map: The current schema map to be updated
    """
    for import_name in ast_import.names:
        if import_name.name == "typing":
            module_element = process_alias(import_name)
            for valid_type in VALID_TYPES:
                element = f"{module_element}.{valid_type}"
                typing_namespace[valid_type].add(element)
                if valid_type == "Any":
                    schema_map[element] = ANY_SCHEMA


def process_import_from(
    ast_import_from: ast.ImportFrom, base_path: str, typing_namespace: TypingNamespace, schema_map: SchemaMap
) -> typing.NoReturn:
    """
    This function accomplishes two things:
    - Process a "from typing import *" kind of import to achieve what the process_import does
    - Process relative imports like "from .foo import *" to recursively find other types via proces_assign and
      proces_class_def. Imports have to be followed in those files to mimic python's import behaviour.

    :param ast_import_from: An ast import from object
    :param base_path: Path to the parent directory of the file that contains the import from statement
    :param typing_namespace: The current typing namespace to be updated
    :param schema_map: The current schema map to be updated
    """
    # Level == 0 are absolute imports. We only follow the one that targets typing
    if ast_import_from.level == 0 and ast_import_from.module == "typing":
        for import_name in ast_import_from.names:
            if import_name.name in VALID_TYPES:
                element = process_alias(import_name)
                typing_namespace[import_name.name].add(element)
                if import_name.name == "Any":
                    schema_map[element] = ANY_SCHEMA
    # Level >= 1 are relative imports. 1 is the current directory, 2 the parent, 3 the grandparent, and so on.
    elif ast_import_from.level >= 1:
        module = f"{ast_import_from.module}.py" if ast_import_from.module else "__init__.py"
        new_base_path = base_path
        for _ in range(ast_import_from.level - 1):
            new_base_path = os.path.join(new_base_path, os.pardir)
        path = os.path.join(new_base_path, module)
        with open(path) as f:
            ast_module = ast.parse(f.read())
        new_typing_namespace = init_typing_namespace()
        new_schema_map = init_schema_map()
        for node in ast_module.body:
            if isinstance(node, ast.Import):
                process_import(node, new_typing_namespace, new_schema_map)
            elif isinstance(node, ast.ImportFrom):
                process_import_from(node, new_base_path, new_typing_namespace, new_schema_map)
            elif isinstance(node, ast.Assign) and node.targets[0].id:
                process_assign(node, new_typing_namespace, new_schema_map)
            elif isinstance(node, ast.ClassDef) and node.name:
                process_class_def(node, new_typing_namespace, new_schema_map)
        for import_name in ast_import_from.names:
            item = new_schema_map.get(import_name.name)
            if item is not None:  # Import could be something we didn't care about and hence didn't put in schema_map
                schema_map[import_name.name] = item


def process_class_def(
    ast_class_def: ast.ClassDef, typing_namespace: TypingNamespace, schema_map: SchemaMap
) -> typing.NoReturn:
    """
    Process a class def statement to update the schema map with types we can define with TypedDict's class-based syntax.
    Example:
    ```python
    import typing

    class Car(typing.TypedDict):
        model: str
        plate: str
    ```

    :param ast_class_def: An ast class def object
    :param typing_namespace: The current typing namespace to be read
    :param schema_map: The current schema map to be updated
    """
    # This supports TypedDict class syntax
    if ast_class_def.bases and get_ast_name_or_attribute_string(ast_class_def.bases[0]) in typing_namespace.get(
        "TypedDict", set()
    ):
        LOGGER.info(f"Processing type {ast_class_def.name} ...")
        properties = {}
        for index, node in enumerate(ast_class_def.body):
            if isinstance(node, ast.AnnAssign):
                properties[node.target.id] = get_json_schema_from_ast_element(
                    node.annotation, typing_namespace, schema_map
                )
        schema_map[ast_class_def.name] = {
            "type": "object",
            "properties": properties,
            "required": list(properties.keys()),
            "additionalProperties": False,
        }


def process_assign(ast_assign: ast.Assign, typing_namespace: TypingNamespace, schema_map: SchemaMap) -> typing.NoReturn:
    """
    Process an assign statement to update the schema map with types we can define with subscripts.
    Example:
    ```python
    import typing

    Car = typing.Dict[str, str]
    ```

    :param ast_assign: An ast assign object
    :param typing_namespace: The current typing namespace to be read
    :param schema_map: The current schema map to be updated
    """
    if (
        isinstance(ast_assign.targets[0], ast.Name)
        and isinstance(ast_assign.value, ast.Subscript)
        and get_ast_name_or_attribute_string(ast_assign.value.value)
        in (
            item
            for values in (typing_namespace[subscript_type] for subscript_type in VALID_AST_SUBSCRIPTS)
            for item in values
        )
    ):
        LOGGER.info(f"Processing type {ast_assign.targets[0].id} ...")
        schema_map[ast_assign.targets[0].id] = get_json_schema_from_ast_element(
            ast_assign.value, typing_namespace, schema_map
        )
