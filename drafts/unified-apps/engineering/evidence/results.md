> ## Documentation Index
> Fetch the complete documentation index at: https://usefused.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Read results and debug failures

> Find an app's output, retrieve a pending result, and inspect a failed request.

## Read a result

An execution response contains `status` and, on success, the `output` returned by your function:

```json theme={null}
{
  "executionId": "<execution-uuid>",
  "appFamilyId": "<app-family-uuid>",
  "version": "1.0.0",
  "status": "succeeded",
  "mode": "live",
  "readHandle": "<caller-held-handle>",
  "output": { "customerId": "cus_123" },
  "createdAt": "<timestamp>",
  "completedAt": "<timestamp>"
}
```

Check `status` before using `output`. HTTP 202 means the request was accepted and may still be queued or running. Keep its `executionId` and `readHandle`, then retrieve the result:

```bash theme={null}
curl "$FUSED_ENGINE_URL/v1/apps/$FUSED_APP_FAMILY_ID/executions/$EXECUTION_ID" \
  -H "Authorization: Bearer $FUSED_APP_TOKEN" \
  -H "X-Execution-Read-Handle: $READ_HANDLE"
```

The URL uses the stable `app_family_id` from deployment. The read handle comes from that execution's response.

## Store data for later lookup

Returning an object from `execute` is enough to produce `output`. Use `fused.db.set(...)` only when you also want a separate execution data document. Declare paths in `fetch.searchable` to make them searchable for callers with the read grant.

Stored data is separate from `output`: it does not appear as a `data` field in the execution response.

## Find a failed request

Open the app's **Requests** tab and select the failed execution. Start with the error and **Execution trace**. Expand **Private diagnostics** when you need the original input, provider response, or stack trace.

<Accordion title="Private diagnostics: permissions, API, and retention">
  In the Unified App's **Requests** tab, open an execution and expand **Private diagnostics**. This shows the original app input, captured output, detailed exceptions, stack traces, and recorded provider-operation requests and responses, including failed provider bodies. New Fused-compiled versions include inline source maps for TypeScript line numbers; older bundles retain their available JavaScript frames. An output that fails validation is retained privately even though it is not returned as a successful public result.

  Access requires `app.unified_app.diagnostics.read`, granted through a custom role on the app family or workspace. Ordinary app read/manage access does not include this permission. The built-in Owner role retains all permissions. Opening Requests also requires the existing `app.unified_app.read` and workspace `audit.read` permissions. Fused checks ownership and the diagnostic grant on every management API read; execution tokens do not authorize this endpoint:

  ```text theme={null}
  GET /apps/{app_id}/executions/{execution_id}/diagnostics
  ```

  Detailed exceptions and provider evidence are encrypted on the retained result and expire with it (currently 24 hours after completion). Diagnostics are never embedded in ordinary activity, public errors, logs, or trace attributes. App inputs and validated outputs use the existing result storage and limits. Captured strings are bounded to 64 KiB and the combined diagnostic record to 1 MiB; the UI labels truncated or incomplete evidence. Provider requests are the operation inputs supplied by the app, not credential-injected HTTP headers. Missing historical evidence is reported as unavailable and never reconstructed by executing the app again.

  Live and rerun executions publish one logical receipt through the existing execution-event worker, including failures before any provider call. Unified App analytics count those logical runs; service/provider usage continues to count physical calls.
</Accordion>

## Execution timings

The request inspector's **Execution trace** shows preparation, initialization, input validation, TypeScript execution, and output validation when those phases ran. The isolated worker measures real elapsed time independently of deterministic app time. The same measurements create OTEL phase spans and are persisted on the canonical receipt, so this view works without an external trace backend or OTEL sampling. Failed runs retain completed and failed-stage timings; unexecuted stages are omitted. TypeScript time includes awaited provider work and must not be added to child-provider durations. Ordinary app/activity permissions cover this metadata; private bodies still require the diagnostic grant.

<Accordion title="OpenTelemetry reference">
  Hosted executions use Fused's configured OpenTelemetry provider. A shared `engine.unified_app.run` span covers live and rerun admission, execution, and persistence; `engine.unified_app.runtime` covers worker execution, including replay. Provider calls inherit that trace context. Canonical request receipts retain the trace and span IDs when tracing is enabled. Runtime spans expose timing, outcome, and a bounded failure phase; raw input, output, errors, and stacks remain in permission-gated private diagnostics. `buildUnifiedApp` does not start another exporter or expose the OpenTelemetry SDK inside the sandbox.
</Accordion>


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.