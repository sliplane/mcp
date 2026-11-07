import asyncio
import unittest

import httpx
from fastmcp import FastMCP

from tool_annotations import (
    add_missing_types,
    api_docs_url,
    customize_openapi_component,
    tool_annotations,
)


def _op(operation_id, summary=None):
    op = {"operationId": operation_id, "responses": {"200": {"description": "ok"}}}
    if summary:
        op["summary"] = summary
    return op


SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "test", "version": "1"},
    "paths": {
        "/projects": {
            "get": _op("listProjects", "List projects"),
            "post": _op("createProject"),
        },
        "/projects/{id}": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
            ],
            "patch": _op("updateProject"),
            "delete": _op("deleteProject"),
        },
        "/postgres": {
            "post": {
                **_op("createPostgres"),
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "version": {
                                        "allOf": [{"enum": [18], "type": "integer"}],
                                        "description": "Major version.",
                                        "default": 18,
                                    },
                                },
                            }
                        }
                    }
                },
            }
        },
        "/hooks/{id}/rotate": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
            ],
            "post": _op("rotateServiceDeployHook"),
        },
    },
}


class ToolAnnotationsTest(unittest.TestCase):
    def test_get_is_read_only(self):
        a = tool_annotations("get", "listProjects", "List projects")
        self.assertEqual(a.title, "List projects")
        self.assertTrue(a.readOnlyHint)
        self.assertFalse(a.destructiveHint)

    def test_title_falls_back_to_operation_id(self):
        a = tool_annotations("get", "listServiceSSHKeys", None)
        self.assertEqual(a.title, "List service SSH keys")

    def test_create_is_not_destructive(self):
        a = tool_annotations("post", "createProject", None)
        self.assertFalse(a.readOnlyHint)
        self.assertFalse(a.destructiveHint)

    def test_destructive_operations(self):
        for method, op in [
            ("delete", "deleteProject"),
            ("put", "putBucketCors"),
            ("patch", "updateProject"),
            ("post", "rotateServiceDeployHook"),
            ("post", "detachSSHKey"),
        ]:
            a = tool_annotations(method, op, None)
            self.assertFalse(a.readOnlyHint, op)
            self.assertTrue(a.destructiveHint, op)

    def test_all_generated_tools_are_annotated(self):
        mcp = FastMCP.from_openapi(
            openapi_spec=SPEC,
            client=httpx.AsyncClient(base_url="http://test"),
            mcp_component_fn=customize_openapi_component,
        )
        tools = asyncio.run(mcp.list_tools())
        self.assertEqual(len(tools), 6)
        for tool in tools:
            a = tool.annotations
            self.assertIsNotNone(a, tool.name)
            self.assertTrue(a.title, tool.name)
            self.assertIsNotNone(a.readOnlyHint, tool.name)
            if not a.readOnlyHint:
                self.assertIsNotNone(a.destructiveHint, tool.name)

        for tool in tools:
            self.assertIn("API reference: https://ctrl.sliplane.io/#api-1/", tool.description)
        postgres = next(t for t in tools if t.name == "createPostgres")
        self.assertEqual(
            postgres.parameters["properties"]["version"],
            {"enum": [18], "type": "integer", "description": "Major version.", "default": 18},
        )

    def test_attach_post_is_not_idempotent(self):
        self.assertFalse(tool_annotations("post", "attachServiceVolume", None).idempotentHint)
        self.assertTrue(tool_annotations("put", "attachSSHKey", None).idempotentHint)

    def test_api_docs_url(self):
        self.assertEqual(
            api_docs_url("post", "/projects/{projectId}/services/{serviceId}/volumes", ["Services"]),
            "https://ctrl.sliplane.io/#api-1/tag/services/POST/projects/{projectId}/services/{serviceId}/volumes",
        )
        self.assertEqual(
            api_docs_url("get", "/ssh-keys", ["SSH Keys"]),
            "https://ctrl.sliplane.io/#api-1/tag/ssh-keys/GET/ssh-keys",
        )
        self.assertEqual(
            api_docs_url("get", "/pricing", []),
            "https://ctrl.sliplane.io/#api-1/GET/pricing",
        )

    def test_add_missing_types(self):
        schema = {
            "type": "object",
            "properties": {
                "version": {"enum": [15, 16]},
                "mixed": {"enum": ["a", 1]},
                "typed": {"type": "boolean"},
                "ref": {"$ref": "#/$defs/X"},
                "union": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "shapes": {
                    "anyOf": [
                        {"properties": {"id": {"type": "string"}}},
                        {"properties": {"name": {"type": "string"}}},
                    ]
                },
                "untyped_union": {"anyOf": [{"type": "string"}, {"enum": [1]}]},
                "unknown": {"description": "no hints"},
                "nested": {
                    "type": "object",
                    "properties": {"level": {"const": 1.5}},
                },
            },
        }
        add_missing_types(schema)
        props = schema["properties"]
        self.assertEqual(props["version"]["type"], "integer")
        self.assertEqual(props["mixed"]["type"], ["integer", "string"])
        self.assertEqual(props["typed"]["type"], "boolean")
        self.assertNotIn("type", props["ref"])
        self.assertEqual(props["union"]["type"], ["string", "null"])
        self.assertEqual(props["shapes"]["type"], "object")
        self.assertNotIn("type", props["untyped_union"])
        self.assertNotIn("type", props["unknown"])
        self.assertEqual(props["nested"]["properties"]["level"]["type"], "number")


if __name__ == "__main__":
    unittest.main()
