

## Node event fields

| `Event` property | Purpose |
|---|---|
| `output` | Pass a value to the next node |
| `route` | Select a conditional edge |
| `message` | Emit assistant text |
| `state_delta` | Update managed session state |

## Framework construction

Harnest compiles managed `Graph` exports automatically. Advanced integrations can call `Graph.build()` during compilation or an active invocation to build for the configured framework.
