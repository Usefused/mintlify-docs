

## Workflow operations

| Operation | Result | Ownership |
|---|---|---|
| `run(name, input)` | `HatchetRun` | Submit and return immediately; the caller owns any later wait |
| `status(job)` | `HatchetRunStatus` | Read `QUEUED`, `RUNNING`, `COMPLETED`, `CANCELLED`, or `FAILED` |
| `wait(job)` | JSON mapping | Persist a continuation and resume when an existing run terminates |
| `run_and_wait(name, input)` | JSON mapping | Prove durable suspension support before submitting and waiting |
| `cancel(job)` | None | Request provider cancellation without claiming worker termination |

## Public contracts

| API | Role |
|---|---|
| `hatchet` / `extension` | Installed `HatchetExtension` singleton |
| `HatchetRun` | Immutable provider run, workflow, and correlation identity |
| `HatchetRunStatus` | Stable provider-neutral terminal and non-terminal status enum |
| `HatchetContext` | Revocable invocation-scoped view used by the extension singleton |
