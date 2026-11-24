---
name: decision-recheck
description: Review SaaS plan promises and observed tasks against explicit user requirements, producing evidence-linked owner, buyer, and marketing/support reports with the Decision Recheck local runner. Use for a bounded product review or a recheck after an offer or source changes.
---

# Decision Recheck

Use the installed `decision-recheck` CLI. From a Decision Recheck checkout, run `uv sync --locked` for setup and prefix the commands below with `uv run`. Read `docs/usage.md` from the runner checkout for the brief format and browser setup. Use the installed CLI's `--help` to confirm the available commands.

## Prepare the case

Capture the application's allowed scope, the relevant plan/locale/currency/billing period, explicit requirements and budget, supplied claims, selected sources, and permitted task actions. Label inferred requirements and obtain the operator's acceptance before treating them as hard constraints.

Create an editable fictional brief with `decision-recheck init --output brief.json`. Before running it for a real product, replace the sample product, scope, permissions, sources, requirements, and claims with the scoped case. Replace fixture tasks with permitted browser recipes and meaningful assertions, or remove them and their references for a document-only review. Confirm each evidence source and task against the user's authorization. For a fictional walkthrough, run `decision-recheck demo --output runs/demo` and label its results as synthetic.

## Run and inspect

Execute `decision-recheck run --brief brief.json --output runs/baseline` in a new or empty output directory. The default run makes no model calls. Use `--live-model` only when provider use and sending scoped evidence are authorized. Read `docs/model-and-privacy.md` for the inputs sent and how to configure the provider. Stop the affected work at authentication, CAPTCHA, unauthorized actions, or exhausted limits and retain the partial result.

Validate with `decision-recheck validate --bundle runs/baseline`. Check the run status, warnings, role reports, and supporting artifacts. A run can exit successfully with partial coverage. Bundle validation checks stored evidence structure and integrity. Preserve the separate execution, support, freshness, fit, and review states. Report a blocked task as an unresolved observation.

## Recheck and report

After a relevant change, validate the baseline, keep the same `case_id`, and run `decision-recheck recheck --baseline runs/baseline --brief brief.json --output runs/recheck` into a separate directory. Validate the new bundle and inspect what was fetched or rerun. Preserve prior decisions and explain which dependencies changed and where evidence remains historical, blocked, or untested.

Return the useful owner fixes, buyer fit/unknowns, and evidence-supported marketing/support corrections. Treat model interpretations as proposals. Share or publish bundles only when authorized, after checking for private content. Keep credentials out of briefs and reports.
