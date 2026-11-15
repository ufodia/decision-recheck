# Validation record — 15 November 2026

This record describes observed checks, not a guarantee of defect-free behavior outside the declared scope.

## Local release verification

| Check | Observed result |
| --- | --- |
| Complete Python, real-browser, HTTP, model-protocol, CLI, and static-demo suite | **195 passed, 0 skipped**, 44.75 seconds |
| Test entry point | `DRC_BROWSER_CHANNEL=chrome uv run python scripts/check.py -q` (set the variable using the host shell's syntax) |
| Python / operating system | CPython 3.12.10 / Windows |
| Actual browser channel | Explicit installed Chrome 157.0.8103.51; separate temporary contexts |
| Browser library / freshness dependency | Playwright 1.65.2 / FreshCtx 0.17.0 |
| Packaging | Source distribution and wheel built successfully |
| Isolated wheel restore | Imported from an isolated installed wheel, generated all four snapshots, validated baseline with zero errors |
| Skill format | Bundled skill-creator validator passed |
| Responsive demo | Six widths from 320 to 1440 pixels, four snapshots, three report views; inspected desktop and mobile captures |

The complete test helper starts an owned loopback static server and stops it after pytest. Running pytest alone skips five optional website tests unless `DRC_DEMO_URL` is supplied.

The locally downloaded Chromium build failed its positive launch control on this Windows installation; no success was inferred from blocked negative tests. Windows release verification explicitly selected the installed Chrome channel. The default bundled Chromium path remains a separate setup requirement.

## Meaningful regression coverage

- Twenty planted business inconsistencies and twenty clean controls.
- Live source changes while the archived evidence remains unchanged; irrelevant scoped edits and changed extractors.
- A/B/C/footer acceptance: marketing alignment resolves after corrected copy while the buyer's budget/export requirements still fail.
- Pure-fixture historical reuse and actual browser-task reruns, with timestamps and executed/reused counts.
- Missing, altered, malformed and traversing artifacts; invalid FreshCtx graph references; unavailable required sources cannot become a globally current report.
- Permission types, finite limits, deadlines, partial runs, invalid model JSON, unknown model evidence IDs, and no hidden retries.
- Actual browser assertions, blocked authentication, read-only request controls, independent contexts, and restricted credential/payment fields.
- Static snapshot/audience tabs, keyboard navigation, evidence/full-report URLs, real JSON download, malformed/oversized import and untrusted text rendering.

## Independent bounded security review

Three reproduced issues were corrected and independently retested: WebSocket requests escaping the HTTP route policy, DNS rebinding between destination validation and connection, and encoded artifact links resolving to a different file than the validated filesystem path.

The retests used owned local servers or instrumented network backends. HTTP Host, TLS SNI, certificate verification, and hostname checking were preserved. No external attack target or private account was used. This is a bounded review, not a security certification.

## Verification limits

Live model request/response behavior was tested with mock transport. No paid inference, model-quality benchmark, real customer study, conversion forecast, or representative human-demand validation was performed.

Source selectors, field mappings, and task assertions are operator supplied. Domain/HTTP controls cannot establish that every endpoint on an approved website is semantically free of side effects. Review the exact task and use a synthetic test environment for permitted interactions.

The repository's GitHub Actions workflow also runs the complete suite on Windows and Linux. The Actions result and tested commit are the authoritative remote evidence; inspect the current run before extending platform claims beyond observed local checks.
