

## Discovery operations

The facade also exposes `inspect()`, `list_tools(cursor=None)`, `list_resources(cursor=None)`, `list_resource_templates(cursor=None)`, `list_prompts(cursor=None)`, and `get_prompt(name, arguments=None)`. Inspection and tool-catalogue listing are developer operations, not additional model tools.

## Connection selection

`MCPClient.connect()` and `FusedMCPClient.connect()` use the framework selected by Harnest during compilation or an active invocation. For standalone discovery, use `harnest mcp inspect CLIENT --project AGENT_DIR --json`.
