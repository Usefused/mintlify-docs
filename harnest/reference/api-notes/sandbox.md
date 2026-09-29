

## Provider data contracts

| Contract | Properties |
|---|---|
| `SandboxRequest` | `code`, `timeout_seconds`, `context`, `input_files`, `execution_id`, `metadata`, `network_policy` |
| `SandboxContext` | Optional `agent_name`, `invocation_id`, `user_id`, and `session_id` |
| `SandboxResult` | `status`, `exit_code`, `stdout`, `stderr`, `output_files`, `metadata` |
| `SandboxFile` | `name`, `content` as bytes or base64 text, and `mime_type` |

## Execution statuses

| Status | Meaning |
|---|---|
| `succeeded` | Execution completed successfully |
| `failed` | Nonzero exit or provider-reported failure |
| `timed_out` | Execution deadline expired |
| `output_limit_exceeded` | Combined output exceeded its budget |
| `cancelled` | Provider-reported cancellation; managed caller cancellation also propagates as an exception |
