## Decision events

Each completed evaluation adds a `decision_result` item to public `output`. Its `value` contains decision/provider versions, typed answers, the policy outcome, duration, and a safe error category when evaluation falls back. Request state, question instructions, and raw provider payloads are excluded. Private graph-to-model inputs are not presented as user turns when restoring conversation history in ADK or LangGraph. SSE and WebSocket use `response.decision_result`; streaming A2A tasks use `metadata.harnest.type: decision_result`. Playground displays an expandable Decision panel. Streamed results appear when the backend next yields an event.

## Raw metadata

Raw mode keeps the normalized fields and adds `raw`. ADK uses its native `LlmResponse` metadata field names. LangGraph namespaces `stream_metadata`, `response_metadata`, `usage_metadata`, and `additional_kwargs` so fields do not collide. The primary message content and Harnest-owned event state are not copied. Native metadata can still contain provider-defined content-like values, including reasoning annotations in `additional_kwargs`.
