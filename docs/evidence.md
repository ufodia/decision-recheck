# Evidence semantics

An evidence bundle is a scoped record, not a universal truth certificate.

| Axis | Meaning |
| --- | --- |
| Execution | What was attempted, completed, blocked, interrupted, or left untested. |
| Evidence basis | Vendor claim, vendor document, task observation, or supplied evidence. |
| Claim support | Whether the captured material supports, conflicts with, or leaves the claim unresolved within scope. |
| Freshness | Whether declared sources were checked, changed, unavailable, or only historical. |
| Fit | Whether an explicit requirement is met, failed, conditional, or unknown. |
| Review | Whether an interpretation is proposed, accepted, rejected, or needs another review. |

## References and integrity

Each material finding must reference actual evidence IDs. Artifact locators are local to the bundle. Missing files, path traversal, invalid references, or mismatched hashes must not be accepted by validation.

An archive hash describes the archived bytes. A live-source freshness check must reread the declared current source. Extractor scope, plan, locale, currency, billing period, and check time matter. A missing selector or an ambiguous response does not silently become current.

Vendor help text can document a feature while a task remains untested. A login gate cannot prove feature absence. Independent source count follows source provenance, not the number of agents repeating it.

## Changes and decisions

Keep old decisions and their original evidence. Link a new check to that baseline and explain the affected conclusion. A plan-price change can invalidate a budget conclusion while leaving an unrelated help finding intact. Correcting copy does not make an expensive plan fit a buyer's budget.

Human review is distinct from automated validation: a valid reference does not prove a correct interpretation. A model-generated confidence number is not a calibrated probability.
