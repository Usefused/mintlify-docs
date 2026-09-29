Use [`Cron`](#cron) for a fixed application-owned declaration. Use [`create`](#create) to obtain a [`CronJob`](#cronjob) for a user-owned schedule. The module functions and `CronJob` methods manage dynamic schedules; `Cron` itself has no pause, resume, or delete methods.

For setup and usage, see [Cron schedules](/harnest/build/scheduled-tasks), [Dynamic schedules](/harnest/build/dynamic-schedules), and [Task and cron storage](/harnest/runtime/task-storage).

## Declare a cron function

[`@cron(...)`](#cron-decorator) creates a queued task for a same-named function in a root `cron/<name>.py` file. Give the function a docstring. A fixed expression uses the supplied `arguments` on each occurrence. Omit the expression for dynamic scheduling only; in that form, do not supply arguments or a non-UTC timezone. Do not stack `@cron` with `@task` because the decorator creates its own task. Direct calls run inline.

`queue="default"` and `max_retries=3` use the [Task validation rules](/harnest/reference/api/task#task-parameters).

## Schedule parameters

| Parameter | Contract |
|---|---|
| `Cron.schedule` / `expression` | Exactly five numeric cron fields: minute, hour, day of month, month, day of week. Supports `*`, comma lists, ascending ranges, and positive `/step`; rejects outer whitespace. |
| `timezone` | `"UTC"` only. Dynamic schedules always use UTC. |
| `Cron.task` | A Harnest task callable discovered in the application. |
| `create(task=...)` | A discovered `@task` or `@cron` callable, or the name of a deployed `@cron` function. A string does not import or register code. |
| `arguments` | Strict JSON-safe keyword arguments matching the target signature. An update replaces the entire mapping. Omit it to preserve current arguments; `None` is not an update mapping. |
| `key` | 1–128 characters. Starts with an ASCII letter or digit; remaining characters may also include `.`, `_`, `:`, `~`, and `-`. Scoped to application and user. |
| `schedule_id` / `CronJob.id` | Opaque `cron_` ID returned by Harnest. Keep it for later owner-scoped operations. |
| `list(after=..., limit=50)` | Returns a tuple ordered by ID. Pass the final job ID as the exclusive next-page cursor; `limit` must be an integer from 1 to 100. |

## Dynamic schedule behavior

Calls require an active managed invocation and a cron-enabled runtime. Register the same durable provider for tasks and cron. Each operation checks the active application and user; retaining a `CronJob` does not grant access outside that scope.

| Operation | Return and behavior |
|---|---|
| `create(...)` | A `CronJob`. Exact retries with the same key and definition return the existing record, including paused or cancelled jobs. A different definition conflicts. |
| `get(id)` | A `CronJob`, or `None` for a missing or unowned ID. |
| `update(id, ...)` / `job.update(...)` | A new `CronJob` snapshot with supplied expression or arguments replaced. Preserves ID, key, owner, and target. |
| `pause(id)` / `job.pause()` | A new snapshot in `paused` state; stops future occurrences. |
| `resume(id)` / `job.resume()` | A new snapshot in `active` state; a paused schedule resumes at its next matching UTC minute. |
| `cancel(id)` / `job.cancel()` | A new snapshot in terminal `cancelled` state. Retains the record. |
| `delete(id)` / `job.delete()` | `True` if an owned record was removed, otherwise `False`. |

`CronJob` is immutable. Assign the returned snapshot, for example `job = await job.pause()`, or fetch it again to read updated fields. Cancelling or deleting a schedule does not cancel tasks already queued or running. Cancelled schedules cannot be updated, paused, or resumed.

## Errors

| Error | When it occurs |
|---|---|
| `CronUnavailableError` | No active managed invocation, no cron-enabled runtime, or a job used with a different runtime. |
| `CronNotFoundError` | Update, pause, resume, or cancel targets a missing or unowned job. |
| `CronConflictError` | Conflicting key reuse, an invalid cancelled-state change, an unavailable target during update, or a conflicting revision. |
| `CronRuntimeError` | Durable persistence or dispatch fails. |
| `ValueError` / `TypeError` | Invalid expression, ID, key, limit, target, or task arguments. |
| `CronStoreConflictError` | Provider-level conflict for custom storage implementations. |

`CronRecord`, `CronStore`, and `CompiledCron` are integration contracts. Application tools normally work with `CronJob` and the module functions.
