# Deploying Sliplane Presets through MCP

Sliplane presets are complete service templates, not a special API deploy source. To deploy one through MCP, retrieve its settings from this guide, resolve its generated values, and then call the normal Sliplane `createService` tool.

The bundled catalog is exported from `sliplane-frontend/utils/presets.ts` at commit `592f238368d2d19bbd6352304e9bbfc8b5c39ef3`. It includes every single-service preset and all of its frontend settings: preset ID, image, protocol, visibility, health check, command, environment variables, and volume mounts. Each entry also includes a `createServiceInput` object translated to the current public API schema used by this MCP server.

## Retrieve a preset

- Call `sliplane_preset_guide()` without an argument to list the available preset IDs.
- Call `sliplane_preset_guide(preset_id="postgres")` to retrieve one deployable template.
- Call `sliplane_preset_guide(preset_id="all")` only when you truly need the complete catalog. It is large.
- The lookup accepts either a preset ID or its display name and is case-insensitive.

## Deployment workflow

1. Identify the target organization, project, and server with the Sliplane MCP tools. If the user belongs to multiple organizations, make sure the intended organization is selected before creating resources.
2. Retrieve the requested preset from this guide.
3. Show the important choices to the user before deployment: service name, public/private exposure, protocol, image, volumes, and any preset values that clearly require user input, such as `your-tunnel-token-here`, `insert-your-api-key-here`, or example email addresses.
4. Resolve every placeholder described below. Do not send unresolved angle-bracket placeholders to the API.
5. Call the MCP `createService` tool using the resolved `createServiceInput`. The public API can create and attach a new volume in the same request using `{ "name": "...", "mountPath": "..." }`; no separate volume call is required for these templates.
6. Check the deployment status and logs. Report generated credentials to the user securely.

The `settings` object is retained to expose the exact frontend preset source, but it is not the public API request shape. Do not pass it directly to `createService`. In particular, the public API does not accept `presetId`; that value is catalog metadata used for discovery and attribution.

## Placeholder rules

- `<SERVER_ID>`: replace with the selected server ID.
- `<PROJECT_ID>`: replace with the selected project ID.
- `<RANDOM_SUFFIX>`: generate one four-character alphanumeric suffix per preset deployment and reuse it everywhere in that template, including service and volume names.
- `<GENERATE_RANDOM_8>`, `<GENERATE_RANDOM_16>`, and `<GENERATE_RANDOM_32>`: generate a cryptographically secure alphanumeric value of the indicated length for each occurrence. Two occurrences are independent unless the placeholder has a more specific shared name.
- `<GENERATE_RANDOM_HEX_32_BYTES>`: generate 32 cryptographically secure random bytes encoded as 64 lowercase hexadecimal characters for each occurrence.
- Named `<OPEN_CLOUD_...>` placeholders: generate one value per distinct placeholder name and reuse it for every occurrence of that exact name. Values whose names end in `_ID` are UUIDs; password and secret values are cryptographically secure 32-character alphanumeric strings.

`$SLIPLANE_DOMAIN` and other `$SLIPLANE_...` strings are platform runtime variables, not guide placeholders. Preserve them exactly.

## MCP createService input shape

Use the generated `createServiceInput`, which follows the public API shape:

```json
{
  "projectId": "project-id",
  "name": "Service-name",
  "serverId": "server-id",
  "deployment": { "url": "registry.example/image:tag" },
  "env": [{ "key": "KEY", "value": "value", "secret": false }],
  "cmd": "",
  "volumes": [{ "name": "new-volume-name", "mountPath": "/data" }],
  "network": { "public": true, "protocol": "http" },
  "healthcheck": "/"
}
```

For private services, `network` contains `public: false` and no protocol. Public TCP or UDP services have a protocol but no HTTP health check. Preserve the retrieved preset's exact generated field set.
