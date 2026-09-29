

## Provider contract

| Member | Required behavior |
|---|---|
| `version` | Stable provider/model revision used in evaluation provenance |
| `capabilities` | A `DecisionCapabilities` value describing the guarantees below |
| `async evaluate(request)` | Return `DecisionResponse` with exactly the requested answer names |

## Provider capabilities

| Capability | Meaning |
|---|---|
| `kinds` | Nonempty `frozenset` of supported `QuestionKind` values |
| `batching` | Can evaluate multiple independent questions against the same state |
| `probabilities` | Every Choice and Score result includes a complete distribution |
| `confidence` | Every Choice and Score result includes native confidence |

## Request and result validation

| Contract | Shape and validation |
|---|---|
| `DecisionDefinition` | Name, version, and a nonempty tuple of uniquely named questions |
| `DecisionRequest` | Definition plus a snapshot of JSON-compatible state; nested mappings and sequences are immutable |
| `ChoiceResult` | Allowed `value`; optional `probabilities` keyed by every option and `confidence` |
| `ScoreResult` | Numeric `value` from `0` to `len(levels) - 1`; optional probability tuple in rubric order and `confidence` |
| `PredicateResult` | `probability` from `0` to `1`; no separate confidence |
| `DecisionEvaluation` | Validated response, optional policy outcome, definition/provider revisions, duration, and optional error category |

## Policy rules

| Policy | Rules |
|---|---|
| `ChoicePolicy` | `routes` covers every option; an optional `minimum_confidence` requires native confidence |
| `ThresholdPolicy` | `value <= lower` selects `below`; `value >= upper` selects `above`; values between select `uncertain` |
