# Live verification of decision-consistent commentary — November 15, 2026

The two remaining ambiguities in the earlier HTTPX review were corrected at the report output boundary. The four roles still make real provider requests, but now select IDs from an application-owned review catalog. They cannot return replacement verdicts or new recommendation wording for the report. See the [contract](commentary-consistency.md) for the exact scope.

## Live runs

All three runs below used new OpenAI `gpt-4.1-mini` responses and the real HTTPX Introduction and QuickStart pages. No recorded response was replayed or substituted. The provider identified the snapshot as `gpt-4.1-mini-2025-04-14`.

| Run | Prompt | New provider requests | Accepted selections | Reported tokens | Result |
| --- | --- | --- | --- | --- | --- |
| A | v5 | 4 | 2 | 10,581 | Partial / CURRENT; two invalid selections were rejected |
| B | v6 | 4 | 4 | 11,274 | Complete / CURRENT; 14 browser actions |
| C, recheck of B | v6 | 4 | 4 | 11,253 | Complete / CURRENT; 24 browser actions |

The first strict run demonstrated rejection rather than a fabricated successful review. The request was clarified with an explicit list of mandatory IDs and a valid minimum answer. Validation remained strict: there was no automatic completion of missing selections, silent response repair, hidden retry, or model fallback. Rejections now also record fixed diagnostic codes without provider response text.

The final baseline and recheck contain **eight distinct new provider response IDs**, none reused from the earlier free-form HTTPX run. Provider-reported usage for those two completed runs totals **22,527 tokens**; all three attempts total **33,108 tokens**. Dollar cost was not measured. The [sanitized execution record](evidence/commentary-consistency-2026-11-15.json) retains ID hashes, timestamps, usage, selected IDs, catalog digests and bundle hashes. Raw credentials and HTML are excluded.

## What was verified

- Every accepted role selection resolves against the rebuilt catalog and current context digest. No accepted proposal has a free-form `summary` or `recommendations` field.
- The three later roles include every formal decision and the mandatory evidence precondition. In particular, owner fit is exactly **`fails`**; no softer readiness conclusion can replace it.
- The report always requires behavior verification **before** a factual documentation change. A desired buyer outcome alone cannot justify rewriting the documented timeout default.
- Captured source facts and all five requirement results remain unchanged: three meet, one fails, one is inconclusive. The unsupported support SLA remains unknown within the selected evidence, not absent across the service.
- A real isolated browser task reran during recheck and passed its three text assertions. B's complete file-tree fingerprint was unchanged after C.
- Three audience reports passed at 1440px and 390px, with no JavaScript errors or horizontal overflow. Expanded task details, evidence anchors, navigation and artifact paths were checked.

In these runs the later roles selected the required minimum catalog items. This demonstrates live contract compliance and report consistency; it is not evidence of novel model insights, independent source corroboration or varying priority judgments.

## Older reports and regression checks

Three new historical HTML views were also rendered from a byte-identical copy of the original free-form HTTPX bundle. All ambiguous legacy prose was excluded with an explicit notice; the original JSON and artifacts were preserved. These historical views were not described as fresh inference.

The final full suite passed **335 tests, zero skipped**, in 106.10 seconds on Windows with installed Chrome. Twenty independent output-boundary cases cover contradictory legacy prose, injected summaries/recommendations/fit/text/catalog fields, invalid references, omitted required decisions and changed fits/source/task/scope. Additional protocol cases verify that rejection retains provider usage and does not retry. Source distribution and wheel builds passed.

The guarantee is bounded: model-selected report items cannot override the current recorded decisions or required follow-up conditions. It does not certify factual source truth, correct operator criteria, full product behavior, cryptographic bundle authenticity or arbitrary legacy model prose.
