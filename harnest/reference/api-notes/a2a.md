

## Client operations

| Method | Network behavior |
|---|---|
| `connect()` | Fetch and validate the Agent Card once |
| `send(...)` | Send one message; optionally poll only the returned Task |
| `stream(...)` | Stream one new interaction; requires `streaming=True` on the client |
| `get_task(task_id)` | Fetch one explicitly named Task |
| `list_tasks(...)` | Fetch one bounded, filtered page on request |
| `cancel_task(task_id)` | Request cancellation of one explicitly named Task |
| `subscribe(task_id)` | Subscribe to one existing Task |

## A2A event fields

The A2A `contextId` maps to the Harnest session ID. A text-input root accepts A2A text parts; a typed-input root requires exactly one structured data part. Harnest projects customer-visible text and structured results back to A2A parts while keeping tool arguments and results inside the executing agent boundary regardless of `tool_activity`. With [`OutputPolicy(thinking=True)`](/harnest/reference/api/output#outputpolicy), a streaming Task emits provider-exposed reasoning as a working-status message whose `metadata.harnest.type` is `thinking`; reasoning is otherwise suppressed. Agent and graph-node lifecycle updates use the same working status with `metadata.harnest.type: agent_activity`; model metadata uses `metadata.harnest.type: agent_metadata`. Set `agent_metadata=AgentMetadataMode.SUPPRESS` to omit those updates and aggregate token counts from the final Message or Task artifact. Answer artifacts can carry `metadata.harnest.agent` attribution. With `OutputPolicy(decision_results=True)`, streaming tasks also publish working-status metadata with `metadata.harnest.type: decision_result` and the typed decision in `metadata.harnest.value`. Decision results are hidden by default.
