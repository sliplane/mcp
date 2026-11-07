"""MCP tool annotations for tools generated from the Sliplane OpenAPI spec."""

import re

from fastmcp.tools import Tool
from mcp.types import ToolAnnotations


# operationId prefixes for write calls that remove, overwrite, invalidate or
# interrupt existing resources and should therefore be flagged as destructive.
DESTRUCTIVE_PREFIXES = (
    "delete",
    "remove",
    "detach",
    "rotate",
    "reset",
    "revoke",
    "purge",
    "clear",
    "suspend",
    "pause",
    "stop",
    "cancel",
    "restore",
    "restart",
    "rescale",
    "put",
    "replace",
    "update",
    "set",
)

# Prefixes for write calls that are safe to repeat with the same arguments.
IDEMPOTENT_PREFIXES = ("set", "put", "update", "attach", "detach", "delete", "remove")


def _title_from_operation_id(operation_id: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|[_\-]+", " ", operation_id)
    words = spaced.split()
    title = " ".join(word if word.isupper() else word.lower() for word in words)
    return title[:1].upper() + title[1:]


def tool_annotations(
    method: str, operation_id: str | None, summary: str | None
) -> ToolAnnotations:
    """Derive MCP tool annotations from an OpenAPI operation."""
    method = method.upper()
    op = (operation_id or "").casefold()
    title = (summary or "").strip() or _title_from_operation_id(operation_id or "")

    if method in {"GET", "HEAD", "OPTIONS"}:
        return ToolAnnotations(
            title=title,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )

    destructive = (
        method == "DELETE"
        or op.startswith(DESTRUCTIVE_PREFIXES)
    )
    idempotent = method in {"PUT", "DELETE"} or op.startswith(IDEMPOTENT_PREFIXES)
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=False,
    )


_JSON_TYPES = (
    (bool, "boolean"),
    (int, "integer"),
    (float, "number"),
    (str, "string"),
    (list, "array"),
    (dict, "object"),
    (type(None), "null"),
)


def _json_type(value) -> str | None:
    return next((name for py, name in _JSON_TYPES if isinstance(value, py)), None)


def _infer_type(schema: dict) -> str | list[str] | None:
    values = list(schema.get("enum") or [])
    for key in ("const", "default"):
        if key in schema:
            values.append(schema[key])
    for example in schema.get("examples") or []:
        values.append(example)
    types = sorted({t for t in map(_json_type, values) if t})
    if "integer" in types and "number" in types:
        types.remove("integer")
    if not types:
        return None
    return types[0] if len(types) == 1 else types


def _structural_type(schema: dict) -> str | None:
    if "properties" in schema or "additionalProperties" in schema:
        return "object"
    if "items" in schema:
        return "array"
    return None


def _member_types(members) -> list[str] | None:
    """Collect the JSON types of composite members, or None if any is untyped."""
    types: list[str] = []
    for member in members:
        if not isinstance(member, dict):
            return None
        member_type = member.get("type") or _structural_type(member)
        if member_type is None:
            return None
        for t in member_type if isinstance(member_type, list) else [member_type]:
            if t not in types:
                types.append(t)
    return types or None


def _type_property(prop: dict) -> None:
    if "type" in prop or "$ref" in prop:
        return
    all_of = prop.get("allOf")
    if isinstance(all_of, list) and len(all_of) == 1 and isinstance(all_of[0], dict):
        # Inline single-member wrappers (OpenAPI's way of adding a description
        # or default next to a schema); the outer keys take precedence.
        del prop["allOf"]
        for key, value in all_of[0].items():
            prop.setdefault(key, value)
        if "type" in prop or "$ref" in prop:
            return
    for key in ("anyOf", "oneOf"):
        if isinstance(prop.get(key), list) and (types := _member_types(prop[key])):
            prop["type"] = types[0] if len(types) == 1 else types
            return
    if "allOf" in prop:
        types = _member_types(prop["allOf"])
        if types and len(types) == 1:
            prop["type"] = types[0]
        return
    if inferred := _structural_type(prop) or _infer_type(prop):
        prop["type"] = inferred


def add_missing_types(schema) -> None:
    """Give untyped property schemas an explicit top-level JSON type, in place.

    Some OpenAPI properties carry no top-level ``type`` (e.g. ``version`` on
    ``createPostgres`` is an ``allOf`` wrapper around an integer enum), which
    MCP directories flag as an untyped parameter.
    """
    if isinstance(schema, list):
        for item in schema:
            add_missing_types(item)
        return
    if not isinstance(schema, dict):
        return
    for props_key in ("properties", "$defs", "definitions"):
        for prop in (schema.get(props_key) or {}).values():
            if isinstance(prop, dict):
                _type_property(prop)
    for key, value in schema.items():
        if key != "enum" and isinstance(value, (dict, list)):
            add_missing_types(value)


def annotate_openapi_component(route, component) -> None:
    """``mcp_component_fn`` hook for ``FastMCP.from_openapi``."""
    if isinstance(component, Tool):
        component.annotations = tool_annotations(
            route.method, route.operation_id, route.summary
        )
        add_missing_types(component.parameters)
