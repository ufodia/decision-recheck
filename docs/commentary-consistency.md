# Decision-consistent model review

Four model roles still review the supplied case. They now select and prioritize application-defined review items instead of supplying free-form report conclusions. This removes the route by which a model could describe a recorded `fails` outcome as ready, or suggest changing a factual statement before verifying the underlying behavior.

## What each role can return

The coordinator supplies a finite review catalog with stable item identifiers for that exact run and role. The model returns only a JSON list of selected identifiers. It cannot supply replacement verdicts, recommendation text, explanations, citations, or revised catalog entries. The requirements researcher selects planning items before tasks; the three later roles select recorded decision items and permitted follow-ups after evaluation.

The application validates the selection against a freshly rebuilt catalog and its digest. Required items cannot be omitted. Unknown or duplicate selections, unsupported fields, changed context, and mismatched evidence references are rejected. The exported report rebuilds the wording from current bundle records rather than trusting saved model text or a stored catalog snapshot.

The resulting priorities are model-selected; their facts, verdicts, scope limits and follow-up preconditions are application-rendered. This is a deliberate output contract, not a claim that an unrestricted language model has become perfectly accurate. A rejected response remains visible as partial work; no response is silently repaired or retried.

## The two corrected ambiguities

- **Readiness:** the displayed fit is the exact recorded `meets`, `fails`, `conditional` or `inconclusive` value. A model cannot replace `fails` with a softer readiness claim.
- **Documentation changes:** a failed criterion leads to review of the criterion and verification of behavior before changing factual documentation. A desired result is not evidence that the documented fact should be rewritten. Missing evidence remains limited to the selected scope.

Source freshness and artifact validation still have their own boundaries. Consistency means the model-selected report items cannot override the recorded decisions; it does not prove that an operator supplied the correct requirements, selected the right source fields, or established complete real-world product behavior.

## Existing saved bundles

Old free-form model proposals remain unchanged in their original JSON. Newly generated HTML excludes that prose with an explicit notice. This applies to all legacy roles, including old task narration. A declaration of the new contract is not trusted by itself: invalid or stale selections are excluded even when the renderer is called directly, and bundle validation reports them as errors.

Re-render a saved bundle into a new HTML path with the ordinary `report` command. That output remains explicitly historical. Re-rendering is not a provider call, and it does not rewrite the original bundle or turn old responses into newly verified model output.

## Live verification

Use the [HTTPX example](../examples/httpx-docs-live.json) and [live configuration instructions](live-site-review.md) to obtain new responses with the strict contract. Each baseline or recheck still requests four roles, with no model narration of deterministic browser tasks. Provider IDs, timestamps and usage distinguish the new requests from retained historical evidence.
