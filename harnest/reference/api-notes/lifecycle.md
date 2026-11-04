

## HTTP agent principal grants

`@lifecycle.http.agent_principal` registers one sync or async function that receives a `ConnectionContext` and an `AuthPrincipal`. Return an `AgentRuntimePrincipal` to grant permissions or `None` to deny the invocation. See [Grant permissions on built-in routes](/harnest/runtime/agent-runtime-principals#grant-permissions-on-built-in-routes).

## Hook control flow

| Return | Effect |
|---|---|
| `context.next()` | Continue unchanged |
| `context.next(replacement)` | Pass a replacement to the next stage |
| `context.finish(result)` | Stop the chain with a final result |
