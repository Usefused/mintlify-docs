Use [`task`](#task) to decorate application work. It returns a [`TaskCallable`](#taskcallable) whose direct call runs inline and whose [`defer`](#taskcallable-defer) method submits queued work. The returned [`TaskHandle`](#taskhandle) exposes status, cancellation, and result access.

For discovery, storage setup, and durable waiting, see [Create and run Tasks](/harnest/build/queued-tasks), [Task and cron storage](/harnest/runtime/task-storage), and [Durable execution](/harnest/runtime/durable-execution).

## Task parameters

| Parameter | Contract |
|---|---|
| `task(function)` | Supports bare `@task` and configured `@task(...)`. The decorated function must have a docstring. |
| `queue="default"` | 1–64 characters. Starts with an ASCII letter; remaining characters may include ASCII letters, digits, `.`, `_`, `~`, and `-`. Set on the decorator, not on `.defer()`. |
| `max_retries=3` | Integer from 0 to 100. Set on the decorator. |
| `defer(*args, **kwargs)` | Bound against the task's original signature and serialized as strict JSON. Positional-only parameters and `*args` are unsupported in the decorated task. |
| `idempotency_key=None` | Optional nonblank text of at most 512 characters. Durable tools derive a replay-stable key when omitted. |
| `schedule_in=None` | Optional finite, non-negative delay in seconds. |

The names `idempotency_key` and `schedule_in` are options on `.defer()`; avoid using them as task input names. Arguments and results must be strict JSON values: no credentials, arbitrary Python objects, non-string object keys, or non-finite numbers. Workers may retry, so task side effects must be idempotent.

## Handle behavior

| Member | Contract |
|---|---|
| `id` | Opaque queue job identifier. |
| `task_name` | Compiler-owned registered task name. |
| `await status()` | Returns the owning runtime's job state. |
| `await cancel()` | Returns whether cancellation succeeded. |
| `await result()` | Returns the JSON-safe completed result. Unfinished work requires an async `@tool(durable=True)` and Harnest-owned checkpointer so the invocation can suspend and resume. |

Handles belong to the compiled runtime that returned them. There is no public handle reconstruction or job-listing API. Calling `.defer()` without an active compiled runtime raises `TaskUnavailableError`; calling the decorated function directly does not require queue storage.

`TaskStore` and `TaskRecord` are storage adapter contracts. `TaskDefinition` and `CompiledTask` describe compiler/runtime registrations. Use [Task and cron storage](/harnest/runtime/task-storage) to choose a production provider; `MemoryTaskStore` does not make work survive a process restart.

## Storage protocols

| Contract | Required operations |
|---|---|
| `TaskStore` | `start`, `close`, `enqueue_task`, `get_task`, `claim_tasks`, `renew_task_lease`, `finish_task`, `cancel_task` |
| `CronStore` | `start`, `close`, `create_cron`, `get_cron`, `list_crons`, `update_cron`, `delete_cron`, `list_due_crons`, `commit_cron_occurrence` |
