

## Exporter factory contract

| Requirement | Behavior |
|---|---|
| Unique `TelemetryExporter.name` | Duplicate names stop runtime startup |
| Synchronous, zero-argument factory | Runs once during runtime bootstrap |
| `traces`, `logs`, or both | Metrics exporters are not supported |
| `order=` | Resolves factories in ascending lifecycle order |
| Startup failure | Already-created exporters are shut down |

## Environment controls

| Variable | Effect |
|---|---|
| `OTEL_SERVICE_NAME` | Sets the service identity |
| `HARNEST_LOG_LEVEL` | Sets the minimum log level; defaults to `INFO` |
| `HARNEST_LOG_CONSOLE=false` | Disables JSON logs on stderr |
| `HARNEST_OTEL_ENABLED=false` | Disables the environment-configured OTLP sink |
| `OTEL_SDK_DISABLED=true` | Disables the environment-configured OTLP sink |
