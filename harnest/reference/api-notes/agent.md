

## Tool declaration

| Property | Rule |
|---|---|
| File | `tools/lookup_order.py` |
| Export | `lookup_order` |
| Description | Docstring or `@tool(description="...")`; distinguish similar parameters explicitly |
| Output validation | Pydantic return annotation or `output_schema` |
| Runtime permission | `@tool(permission="tickets.read")`; required when the tool must be available under an Agent Runtime Principal |
| Unit testing | Call the decorated function directly |

## Private client input contract

| Contract | Behavior |
|---|---|
| Consumer | Async application handler; must return `None` |
| Model response | Required JSON object in `response`, frozen when the decorator is applied |
| Accidental return or exception | Fail with a generic error; no returned value or original exception chain reaches the framework |
| Storage | Process-local, one-time delivery; no automatic asset staging, history, checkpoint, or telemetry projection of the input |
| Lifetime | Cleared on consumption or cancellation; expired, cancelled, and consumed requests reject subsequent submissions |
| Timeout | `timeout_seconds`, default `300` |
| Durable tools | Rejected; private input cannot use a persisted tool continuation |
