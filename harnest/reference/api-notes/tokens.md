

## Policy settings

| Setting | Default | Behaviour |
|---|---|---|
| `enabled` | `True` | `False` bypasses counting, observers, reductions, and enforcement. |
| `observe` | `True` | Emit reports to `observer`, or the `harnest.tokens` logger. |
| `enforce` | `False` | Stop calls that exceed configured budgets and apply the output ceiling. |
| `max_input_tokens` | `None` | Maximum counted input after reductions, including system instructions and tool descriptors. |
| `context_window` | `None` | Maximum counted input plus reserved output capacity. |
| `reserve_output_tokens` | `0` | Capacity reserved for the response; Harnest reserves the larger of this value and `max_output_tokens`. |
| `max_output_tokens` | `None` | Provider output ceiling; preserves a stricter existing native limit. |
| `output_token_parameter` | `None` | LangGraph override for `max_tokens`, `max_completion_tokens`, or `max_output_tokens`. By default Harnest uses an existing request parameter, then `max_tokens`. ADK always uses its native `max_output_tokens` field. |
| `max_model_calls` | `None` | Maximum admitted model attempts per agent per runtime invocation, including failed attempts. |
| `keep_recent_turns` | `None` | Keep this many recent human turns and their model/tool exchanges; pin system/developer instructions. |
| `max_tool_result_chars` | `None` | Cap each tool-response text string, with a truncation marker. This is a per-string character ceiling, not a total JSON or token ceiling. |

## Strategy callbacks

| Callback | Input | Return |
|---|---|---|
| `count_tokens` | Detached `TokenRequest` | `TokenCount(tokens=..., estimated=...)` |
| `request_transform` | Detached `TokenRequest` | A `TokenRequest`, for example using `dataclasses.replace`. |
| `tool_selector` | Detached `TokenRequest` after transformation | A list or tuple of existing tool names to expose on this call. |
| `observer` | Content-free `TokenReport` | No return value required. |
