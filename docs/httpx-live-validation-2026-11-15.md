# Four-role live review of HTTPX — November 15, 2026

This review exercised a different real website: the official [HTTPX introduction](https://www.python-httpx.org/) and [QuickStart](https://www.python-httpx.org/quickstart/). Every model proposal in the runs recorded here came from a new OpenAI Chat Completions request. No recorded-response replay, mock response transport, or substituted model output was used in these live runs.

## Scope and independent source checks

The [checked-in brief](../examples/httpx-docs-live.json) reviews documentation for adopting HTTPX. It selects three small fields from two public pages and performs three text assertions in an isolated browser. Reads are restricted to `www.python-httpx.org`; external assets and non-read operations are blocked. It does not execute HTTPX examples, measure real network timeouts, assess support service performance, or access accounts.

An independent source review established these expectations before model calls:

| Supplied criterion | Expected result | Evidence boundary |
| --- | --- | --- |
| Introduction documents synchronous and asynchronous APIs | Meets | The selected introduction paragraph describes both interfaces |
| Introduction identifies the optional HTTP/2 installation extra | Meets | The selected dependency entry identifies the optional extra |
| QuickStart documents a five-second default for network inactivity | Meets | Selected timeout paragraph and fresh text assertions |
| QuickStart states that network inactivity has no default timeout | Fails | This operator-supplied criterion conflicts with the documented default |
| Selected documentation establishes a two-hour support response SLA | Inconclusive | This field is not established in the selected evidence |

The incompatible timeout-free criterion is a control of requirement fit, not a claim that HTTPX is defective. Missing SLA evidence does not prove the absence of an SLA everywhere. No advertising or support claim comparisons were supplied, so marketing alignment remains inconclusive. The owner outcome fails because a hard adoption criterion is unmet.

## Live runs and corrections

The configured model alias was `gpt-4.1-mini`; provider responses identify the actual snapshot separately. Each live run requests exactly four roles: requirements researcher, offer/support analyst, evidence reviewer and report writer. The browser task actor records deterministic observations without a model narration.

Baseline A completed with four fresh responses, 7,795 reported tokens and 14 browser actions. Recheck B fetched the live sources again and completed with four different responses, 7,731 tokens and 24 browser actions. Both were CURRENT, their evidence bundles validated, the three browser assertions passed, and all five requirement results matched the independent expectations. The baseline file-tree fingerprint remained unchanged.

Reviewing every proposal exposed a recommendation problem despite correct formal results: B suggested changing documentation to satisfy a timeout-free requirement without independent evidence that the package behavior had changed. A also contained redundant documentation advice and imprecise wording about the purpose of its text-reading task. Original A/B outputs were retained.

Prompt revision `scoped-evidence-v4` adds a general boundary: conflicting operator criteria must not become alleged vendor contradictions, documented facts must not be rewritten merely to satisfy a desired result, and task purpose must stay within the declared title and recorded steps. These instructions are regression-tested as request boundaries; a unit test cannot establish natural-language accuracy. The corrected prompt was then checked with another new real-provider run, as recorded below.

Successful-response metadata now preserves optional bounded response IDs, provider model snapshots, creation timestamps and per-role token totals. Configured aliases remain separate. This improves traceability rather than constituting a provider signature or factual-accuracy guarantee; raw headers and credential files are excluded.

## Final fresh four-role result

Run C used four **new** v4 provider responses and independently fetched the same live sources again. It completed as **CURRENT**, with 8,077 reported tokens, 24 browser actions, one executed task and three passed text assertions. All five formal outcomes matched the source oracle. Both A and B file-tree fingerprints were unchanged. No role or stored response was removed, edited or replayed in C.

Across A/B/C there were **12 distinct provider response IDs**, 12 real inference requests and **23,603 provider-reported tokens**. All responses identified `gpt-4.1-mini-2025-04-14` as the provider snapshot behind the configured alias. The [sanitized execution record](evidence/httpx-live-2026-11-15.json) contains run/bundle hashes, response-ID hashes, timestamps, per-role usage and results. Dollar cost was not measured. Mock transports remain confined to ordinary protocol tests, outside these live runs.

An independent review read every summary and recommendation from all four C roles. The main source facts and requirement outcomes were retained, the earlier invented task-purpose wording was gone, and the reviewer explicitly instructed against changing facts without behavioral verification. The generated prose is still imperfect:

- The reviewer also used an ambiguous suggestion to align documentation “or” seek verification. The correct action is to verify behavior before changing a factual statement, or revisit the incompatible operator criterion.
- The writer's final wording “ready with exceptions” is softer than the formal owner result. **The formal owner fit is `fails`**; this commentary does not override it.
- References to an absent SLA mean absent from the selected evidence, not proven absent across the entire service or website.

These are recorded limits, not silently corrected quotations or a claim of perfect model accuracy. The HTML keeps unverified commentary separate from computed decisions and actual task records. Three audience reports passed at both 1440px and 390px widths: no JavaScript errors or page overflow, valid evidence/navigation links, and readable expanded task details. Original bundles were preserved during review.

## Reproduce and interpret

Use the [live-site walkthrough](live-site-review.md#review-a-different-real-website). Output paths must be new. Running those commands with a real provider creates new calls and may incur usage charges; it does not reuse these saved proposals.

Task assertions establish selected text presence. The model receives selected source values and recorded events, not screenshot pixels or full raw pages. Requirement comparisons, observed task outcomes, source freshness, artifact integrity and fallible generated commentary remain distinct. Raw runs stay outside Git because local browser/security-software injection may introduce machine-specific URLs.
