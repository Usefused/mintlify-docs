

## Hook control flow

| Return | Effect |
|---|---|
| `context.next()` | Continue unchanged |
| `context.next(replacement)` | Pass a replacement to the next stage |
| `context.finish(result)` | Stop the chain with a final result |
