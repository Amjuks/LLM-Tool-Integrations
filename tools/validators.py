import jsonschema
from typing import Any, Dict


def validate_schema(instance: Any, schema: Dict[str, Any]) -> None:
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        messages = [format_error(error) for error in errors]
        raise ValueError("Schema validation failed: " + "; ".join(messages))


def format_error(error: jsonschema.ValidationError) -> str:
    path = ".".join(str(p) for p in error.absolute_path)
    schema_path = ".".join(str(p) for p in error.absolute_schema_path)
    if path:
        message = f"{path}: {error.message}"
    else:
        message = error.message
    if schema_path:
        message = f"{message} (schema path: {schema_path})"
    return message


def validate_tool_dispatch(selection: Any, registry: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(selection, dict):
        raise ValueError("Tool selection response must be a JSON object.")

    if "tool_required" not in selection:
        raise ValueError("Missing field 'tool_required'.")
    if not isinstance(selection["tool_required"], bool):
        raise ValueError("Field 'tool_required' must be true or false.")

    tool_required = selection["tool_required"]
    tool_name = selection.get("tool_name")
    tool_input = selection.get("tool_input", {})

    if tool_required:
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("tool_name is required when tool_required is true.")
        if tool_input is not None and not isinstance(tool_input, dict):
            raise ValueError("tool_input must be an object.")
        tool = next((tool for tool in registry.get("tools", []) if tool.get("name") == tool_name), None)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' is not present in the registry.")
        # Ignore any partial tool_input supplied during tool selection.
        # A second AI call will format the final tool_input exactly to the selected tool schema.
        tool_input = {}
    else:
        tool_name = None
        tool_input = {}

    return {
        "tool_required": tool_required,
        "tool_name": tool_name,
        "tool_input": tool_input,
    }
