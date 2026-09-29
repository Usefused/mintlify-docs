Use `from harnest import context` for capabilities bound to the current managed invocation. Access to a capability does not extend its lifetime beyond that invocation.

## Invocation capabilities

These attributes are resolved at runtime rather than stored as module globals. Use the linked types for their methods; accessing a managed property during import or outside its required runtime raises an availability error.

| Attribute | API |
|---|---|
| `context.current()` | [`AgentContext`](#agentcontext): invocation identity and named resources. |
| `context.agent` | [`LocalAgentRuntime`](#localagentruntime): start or access a root agent session from task execution. |
| `context.session` | [`SessionContext`](#sessioncontext): current session data. |
| `context.memory` | [`MemoryContext`](#memorycontext): user-scoped long-term memory. |
| `context.assets` | [`ScopedAssets`](#scopedassets): user/session-scoped assets. |
| `context.sandboxes["name"]` | [Named sandbox execution](#sandboxhandle): execute only through an assigned sandbox. |
| `context.extensions("name")` | [`ExtensionContext`](/harnest/reference/api/extensions#extensioncontext): installed extension capability; see its typed extension reference. |
| `context.storage` | [`StorageContext`](#storagecontext): named custom storage. |
| `context.credentials` | [`CredentialContext`](/harnest/reference/api/credentials#credentialcontext): credential resolution. |
| `context.mcp` | [`MCPContext`](/harnest/reference/api/mcp#mcpcontext): governed MCP calls. |
| `context.skills` | [`SkillAccess`](/harnest/reference/api/skills#skillaccess): current agent's skills. |
| `context.decisions` | [`DecisionContext`](/harnest/reference/api/decisions#decisioncontext): registered typed decisions. |

Identity properties such as `context.user_id`, `context.session_id`, and `context.invocation_id` read from the active `AgentContext`. See [Agent runtime principals](/harnest/runtime/agent-runtime-principals) for authorization and [Tasks](/harnest/build/queued-tasks#start-a-fresh-agent-session) for task-initiated agent calls.

## Memory operations

| Operation | Behavior |
|---|---|
| `put(key, content, ...)` | Explicitly insert or replace one scoped record |
| `get(key)` | Return a live record or `None` |
| `list(limit=20, after=None)` | Return a bounded page in ascending key order |
| `search(query, limit=20, after=None)` | Return literal, case-sensitive content matches |
| `delete(key, ...)` | Remove the record and its index references; return whether it existed |

## Session operations

| Operation | Behavior |
|---|---|
| `get(key, default=None)` | Returns a detached value |
| `set(key, value)` | Replaces one value |
| `update(values)` | Writes several keys under one session lease |
| `delete(key)` | Deletes one key and returns whether it existed |
| `namespace(name)` | Isolates domain or plugin keys |
