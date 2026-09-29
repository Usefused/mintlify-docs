

## Metric return values

| Return value | Scoring policy |
|---|---|
| `MetricScore(0.9, "Evidence")` | Scores the conversation once, on its final actual turn; earlier turns remain unscored |
| A list or tuple of `MetricScore` values | Requires one value per actual turn; the overall score is the mean of scored turns |
| `MetricScore(None, "Evidence unavailable")` | Marks the score `NOT_EVALUATED`; an entirely unscored metric cannot pass |
| Native ADK `EvaluationResult` | Passes through unchanged for advanced result control |

## Native scorer contract

```python
from google.adk.evaluation.conversation_scenarios import ConversationScenario
from google.adk.evaluation.eval_case import Invocation
from google.adk.evaluation.eval_metrics import EvalMetric
from google.adk.evaluation.evaluator import EvaluationResult

def required_location_terms(
    metric: EvalMetric,
    actual: list[Invocation],
    expected: list[Invocation] | None,
    scenario: ConversationScenario | None,
) -> EvaluationResult:
    """Signature only; see Create custom evals for the complete implementation."""
    ...
```

The evaluator calls the function with four positional values:

| Argument | Value |
|---|---|
| `metric` | Metric name, criterion, and registered function path; read the threshold from `metric.criterion.threshold`, not the deprecated `metric.threshold` field |
| `actual` | Ordered invocations captured from one case, not the whole eval set |
| `expected` | Golden invocations for a static case, otherwise `None` |
| `scenario` | ADK `ConversationScenario` for a simulated case, otherwise `None` |

Scorers may be sync or async; use async I/O for network calls. They receive ADK evaluation inputs, not a Harnest runtime or storage client.

Actual and golden invocation counts can differ. Check the index before accessing `expected[index]`, and handle `expected=None` for simulations.

## Native result contract

A scored `EvaluationResult` requires one ordered `PerInvocationResult` per actual invocation. Entirely `NOT_EVALUATED` results are exempt.

| Result field | Contract |
|---|---|
| `overall_score` | The aggregate score, or `None` when not evaluated |
| `overall_eval_status` | An explicit ADK `EvalStatus` consistent with the score and threshold |
| `per_invocation_results` | One row per actual turn for a scored metric |
| Each row's `actual_invocation` | The corresponding captured invocation |
| Each row's `expected_invocation` | The matching golden invocation when available, otherwise `None` |
| Each row's `score` and `eval_status` | The turn's numeric score and explicit status, or `None` and `NOT_EVALUATED` when unscored |

Keep aggregate and per-turn scores consistent: the CLI gate compares the mean of scored turns with the threshold.

For final-turn scoring, mark earlier rows `NOT_EVALUATED` and use the last turn’s score as the overall score. Entirely unscored metrics cannot pass. See the [walkthrough](/harnest/build/evaluations/create-custom-evals) for mean-of-turns scoring.

## EvalRunResult envelope

The current contract is identified by:

```json
{
  "apiVersion": "harnest.dev/v1alpha1",
  "kind": "EvalRunResult"
}
```

Branch consumers on `apiVersion`. The result schema is versioned independently from the installed ADK's nested case models.

```json
{
  "apiVersion": "harnest.dev/v1alpha1",
  "kind": "EvalRunResult",
  "createdAt": "2026-09-03T10:30:00+00:00",
  "framework": "adk",
  "trajectory": "business",
  "status": "failed",
  "summary": {
    "suiteCount": 1,
    "caseCount": 1,
    "passedCases": 0,
    "failedCases": 1,
    "notEvaluatedCases": 0
  },
  "evalSetResults": [
    {
      "appName": "harnest_eval",
      "evalSetId": "city-facts",
      "status": "failed",
      "evalCaseResults": [
        {
          "evalSetId": "city-facts",
          "evalId": "verify_paris",
          "finalEvalStatus": "failed",
          "overallEvalMetricResults": [
            {
              "metricName": "response_match_score",
              "threshold": 0.8,
              "score": 0.6,
              "evalStatus": "failed",
              "details": {"rubricScores": null}
            }
          ],
          "evalMetricResultPerInvocation": [
            {
              "actualInvocation": {},
              "expectedInvocation": {},
              "evalMetricResults": []
            }
          ],
          "sessionId": "___eval___session___...",
          "sessionDetails": {},
          "userId": "eval-user"
        }
      ]
    }
  ]
}
```

The abbreviated empty invocation and session objects above stand in for complete ADK-shaped data in a real result.

### Top-level fields

| Field | Meaning |
|---|---|
| `createdAt` | UTC creation time |
| `framework` | Agent runtime: `adk` or `langgraph`. Both use ADK's evaluation contract. |
| `trajectory` | Effective `business` or `strict` policy |
| `status` | `passed`, `failed`, `not_evaluated`, or `error` |
| `summary` | Suite and case counts by status |
| `evalSetResults` | Ordered suite results and their complete case results |
| `error` | Infrastructure exception type and a fixed privacy-safe message; present when `status` is `error` |

### Case diagnostics

Each `evalCaseResults` item preserves:

- Overall result, score, criterion, and details for every metric.
- Per-invocation metric results.
- Complete actual invocations and optional expected invocations.
- User content, final responses, intermediate events, tool evidence, and applicable rubrics carried by those invocations.
- Evaluator session ID, user ID, and session details, including state and recorded events.
- Rubric scores and rationales in each metric's `details.rubricScores` when the evaluator supplies them.

Statuses are lowercase names. `not_evaluated` means no score; the CLI averages scored turns only.

### Infrastructure errors

If evaluation has started and a provider, adapter, or evaluator raises an infrastructure error, Harnest emits or writes the partial result before reporting the original command failure. Its top-level error excerpt looks like this:

```json
{
  "status": "error",
  "error": {
    "type": "RuntimeError",
    "message": "evaluation infrastructure failed"
  },
  "evalSetResults": []
}
```

Harnest omits the original exception message, traceback, and internals from this field because provider errors can contain credentials or request content. Failures before the eval lane starts, such as compilation, unit tests, or invalid configuration, may produce no result file.

`EvaluationExecutionError` means execution or scoring failed without metric results. Follow its safe diagnostic message and inspect the local traceback. Fix runtime problems before reassessing quality.

## Judge configuration

| Property | Default | Applies to | Purpose |
|---|---:|---|---|
| `threshold` | Required | Every metric | Pass boundary |
| `judgeModelOptions.judgeModel` | Configured `OPENAI_MODEL` | Model-judged metrics | Omit to use the shared compatible API; explicit IDs select an ADK model provider |
| `judgeModelOptions.judgeModelConfig` | None | Model-judged metrics | Google GenAI generation options for judge calls |
| `judgeModelOptions.numSamples` | `5` | Final-response match, rubric metrics, and simulator-quality metrics | Judge calls per invocation before aggregation |
| `judgeModelOptions.parallelismLimit` | `1` | Final-response match and rubric metrics | Maximum concurrent judge calls |
| `includeIntermediateResponsesInFinal` | `false` | `final_response_match_v2` and rubric-based final response quality | Include visible text emitted before tool calls with the final output |
