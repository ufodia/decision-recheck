---
name: decision-recheck
description: Review SaaS plan promises and observed tasks against explicit user requirements, producing evidence-linked owner, buyer, and marketing/support reports with the Decision Recheck local runner. Use for a bounded product review or a recheck after an offer or source changes.
---

# Decision Recheck

Use the installed `decision-recheck` CLI from this repository. Inspect `--help` and the generated brief rather than inventing flags or treating a fictional example as live evidence.

## Prepare the case

Capture the application's allowed scope, the relevant plan/locale/currency/billing period, explicit requirements and budget, supplied claims, selected sources, and permitted task actions. Label inferred requirements and obtain the operator's acceptance before treating them as hard constraints.

Create the brief with `decision-recheck init --output brief.json`. Review it against the user's request and the repository's `docs/usage.md`. For an explanation without live access, run `decision-recheck demo --output runs/demo`; disclose that the data is fictional.

## Run and inspect

Execute `decision-recheck run --brief brief.json --output runs/baseline` within the user's authorized scope. The runner enforces limits; skill instructions cannot grant permissions or substitute for runtime checks. Stop at authentication, CAPTCHA, unauthorized actions, or exhausted limits and retain the partial result.

Validate with `decision-recheck validate --bundle runs/baseline`. Inspect the role reports and actual evidence artifacts. Preserve the separate execution, support, freshness, fit, and review states. Do not count repeated citations as independent confirmation or a blocked task as a failed product capability.

## Recheck and report

Use `decision-recheck recheck --baseline runs/baseline --brief brief.json --output runs/recheck` after a relevant change. Current-source checks must read the scoped source; an unchanged archive is insufficient. Preserve old decisions, explain changed conditions, and distinguish untested work from observed outcomes.

Return the useful owner fixes, buyer fit/unknowns, and evidence-supported marketing/support corrections. Treat model interpretations as proposals. Share or publish bundles only when authorized, after checking for private content. Keep credentials out of briefs and reports.
