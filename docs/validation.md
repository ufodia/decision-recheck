# Validation record — 15 November 2026

This record describes observed checks, not a guarantee of defect-free behavior outside the declared scope.

## Local release verification

| Check | Observed result |
| --- | --- |
| Complete Python, real-browser, HTTP, model-protocol, CLI, and static-demo suite | **301 passed, 0 skipped**, 126.55 seconds |
| Test entry point | `DRC_BROWSER_CHANNEL=chrome uv run python scripts/check.py -q` (set the variable using the host shell's syntax) |
| Python / operating system | CPython 3.12.10 / Windows |
| Actual browser channel | Explicit installed Chrome 157.0.8103.51; separate temporary contexts |
| Browser library / freshness dependency | Playwright 1.65.2 / FreshCtx 0.17.0 |
| Packaging | Source distribution and wheel built successfully |
| Isolated wheel restore | Imported from an isolated installed wheel, generated all four snapshots, validated baseline with zero errors |
| Skill format | Bundled skill-creator validator passed |
| Responsive demo | Latest review: four widths (320, 390, 768, 1440), four snapshots, three report views; 48 combinations without overflow or JavaScript errors, plus inspected desktop/mobile captures |

The complete test helper starts an owned loopback static server and stops it after pytest. Running pytest alone skips eight optional website tests unless `DRC_DEMO_URL` is supplied.

## Follow-up functional audit

The second review reproduced defects before adding fixes. Owner summaries now retain inconclusive or conditional requirements and include positive requirement evidence. Empty browser text assertions are rejected. Malformed brief/bundle records return validation errors, unexpected fixture values remain unknown, and UTF-8 BOM JSON from Windows editors is accepted. A real browser attempt is no longer labeled wholly fictional merely because its documentary sources are inline.

An independent CLI journey exercised `init → run → validate → report → source change → recheck → validate` against a mutable owned loopback source. The original baseline remained byte-identical and network requests stayed GET-only. Numeric price comparisons require normalized JSON numbers; HTML selector text is not automatically parsed as currency.

Website regressions cover failed catalog loading followed by local import, preserving an import during a late network failure, retrying successfully, and selecting the changed offer before loading finishes. The main call to action now opens the promised snapshot. Eight complete browser tests passed locally.

The subsequent live-site audit reproduced an assertion that failed on a loading placeholder. Bounded waits now observe delayed text; permanent mismatches, disappearing targets and expired deadlines retain distinct outcomes. A real recheck also exhausted the browser budget by validating one HTML source separately for many prior decisions. Sharing a fresh read strictly within the baseline-comparison batch resolved that issue, while an independent final source check still blocks late drift. The actual deployed-site recheck completed with 24 browser actions, one passed task, zero warnings and a valid CURRENT bundle.

Additional model regressions cover modern/explicit-legacy token parameters, retained provider usage on rejected output, role-specific evidence context, source/model-mode separation, escaped recommendations and secret-safe failure diagnostics. Final source validation is included in usage counters. Local credential-file parsing rejects invalid lines without echoing their contents.

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

## Real-provider review

OpenAI `gpt-4.1-mini` was exercised against the actual deployed public site. Ten proposals were returned across two successful provider runs, with 20,498 reported tokens in total. The final recorded live run was complete/CURRENT with 24 browser actions, three passed text assertions and valid evidence. All five declared requirement results matched the independent source review.

One role nevertheless produced incorrect natural-language task narration. The default pipeline now records browser execution deterministically and uses four explicitly unverified model review roles. See the [complete dated review](live-validation-2026-11-15.md) for the failed attempts, exact semantic errors, corrections, replay-versus-live distinction and remaining limits. Successful transport, JSON or citation validation is not a factual-accuracy certificate.

The revised historical views of the unchanged real-provider bundle passed six layout checks: three audiences at 1440 and 390 pixels. Recorded observations, navigation, citations and artifact links remained valid; no JavaScript errors or page overflow occurred with details collapsed or expanded. The incorrect legacy task narration was excluded with an explicit JSON-retention notice. A separate network-disabled replay exercised the four retained provider responses without claiming new inference or changing original evidence.

## Verification limits

The subsequent [HTTPX four-role review](httpx-live-validation-2026-11-15.md) used a different real website and **12 new provider responses**, including a fresh four-role run after the recommendation-boundary fix. All live runs used the normal provider network transport; no stored responses were replayed. The final case retained correct formal outcomes and passed six report-layout checks. Its record also identifies remaining free-form wording limits, which do not override deterministic decisions.

The routine suite uses mock transport for model protocol checks; the separate dated review used real provider inference. No broad model-quality benchmark, real customer study, conversion forecast, or representative human-demand validation was performed. Free-form model commentary remains fallible and requires human review.

Source selectors, field mappings, and task assertions are operator supplied. Domain/HTTP controls cannot establish that every endpoint on an approved website is semantically free of side effects. Review the exact task and use a synthetic test environment for permitted interactions.

The repository's GitHub Actions workflow also runs the complete suite on Windows and Linux. The Actions result and tested commit are the authoritative remote evidence; inspect the current run before extending platform claims beyond observed local checks.
