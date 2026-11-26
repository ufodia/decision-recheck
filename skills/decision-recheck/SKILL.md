---
name: decision-recheck
description: Review SaaS plan promises and observed tasks against explicit user requirements, producing evidence-linked owner, buyer, and marketing/support reports with the Decision Recheck local runner. Use for a bounded product review or a recheck after an offer or source changes.
---

# Decision Recheck

## Set up the runner

This skill can be installed separately from the runner. If `decision-recheck --help` works, use that CLI. Otherwise, use an existing Decision Recheck checkout or clone [ufodia/decision-recheck](https://github.com/ufodia/decision-recheck) into a workspace location. With Python 3.12 and uv available, run `uv sync --locked --project "<runner-checkout>"`. From the case workspace, run the commands below as `uv run --locked --project "<runner-checkout>" decision-recheck …` so the case paths stay relative to that workspace. Replace the placeholder with the actual checkout path.

Use `docs/usage.md` in the runner checkout for field mappings, browser setup, and recovery, or open the [usage guide](https://github.com/ufodia/decision-recheck/blob/main/docs/usage.md) when you only have the CLI. Try `decision-recheck demo --output runs/demo` and open `runs/demo/index.html` to learn the three views without a browser installation or model key. Label the fixture as fictional.

## Prepare the case

Capture the allowed scope, selected plan and locale, currency, billing period and tax basis, and the buyer's budget. Mark each supplied requirement as required or optional. Keep an inferred condition provisional until the operator accepts it as a hard constraint.

Create an editable fictional brief with `decision-recheck init --output brief.json`. Replace sample sources, requirements, claims, and permissions with the actual case. Map each criterion to a named field and an expected value of the same type. Compare a budget with a numeric field on the same commercial basis. Link a requirement to a permitted browser task only when that task can establish part of the criterion. For a document-only case, remove the fixture tasks and their `task_id` links. Keep capture and action scope within the user's authorization.

## Run and inspect

Execute `decision-recheck run --brief brief.json --output runs/baseline` in a new or empty output directory. The default run makes no model calls. Use `--live-model` only when provider use and sending scoped evidence are authorized. Read `docs/model-and-privacy.md` for the inputs sent and how to configure the provider. Stop the affected work at authentication, CAPTCHA, unauthorized actions, or exhausted limits and retain the partial result.

Validate with `decision-recheck validate --bundle runs/baseline`. Check the run status, warnings, role reports, and supporting artifacts. A run can exit successfully with partial coverage. Bundle validation checks stored evidence structure and integrity. Preserve the separate execution, support, freshness, fit, and review states. Report a blocked task as an unresolved observation.

## Recheck and report

After a relevant change, validate the baseline, keep the same `case_id`, and run `decision-recheck recheck --baseline runs/baseline --brief brief.json --output runs/recheck` into a separate directory. Validate the new bundle and inspect what was fetched or rerun. Preserve prior decisions and explain which dependencies changed and where evidence remains historical, blocked, or untested.

For each requested audience, lead with the decision and link the reported evidence or recheck needed to make it.

- **Owner** — Give the highest-impact discrepancies first. Identify the affected plan, source, or task and specify what to reproduce and what result would verify the fix. A buyer preference can be unmet even when the product works as described.
- **Buyer** — Show which required criteria pass, fail, or remain unresolved. Name the field, commercial term, or task result that would resolve each material unknown. Keep optional preferences separate when deciding whether a plan works for the buyer.
- **Marketing/support** — Identify the supplied statement and its product-side reference. Give a scoped correction only as far as the evidence supports it. Verify behavior before changing a factual claim. For unresolved comparisons, request the exact missing source or field before publishing a claim.

Treat model interpretations as proposals. Share or publish bundles only when authorized, after checking for private content. Keep credentials out of briefs and reports.
