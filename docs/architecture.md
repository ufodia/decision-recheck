# Architecture

Decision Recheck is a local SaaS audit application layer. It reuses FreshCtx for evidence dependencies and freshness, and Playwright for browser execution. It does not implement a second general-purpose dependency engine.

## Data flow

1. Accept and validate an operator-reviewed brief: scope, requirements, supplied claims, source descriptions, task recipes, and budgets.
2. Capture selected source observations and permitted task events in isolated sessions.
3. Store raw evidence separately from structured findings, with bundle-local locators and integrity hashes.
4. Connect domain findings and decisions to upstream observation/reasoning references.
5. Produce owner, buyer, and marketing/support views from the same validated records.
6. On an explicit recheck, fetch current scoped evidence, retain the baseline, and report affected decisions.

Current-status report output must be gated by fresh source validation immediately before the actual writer runs. Historical and partial reports remain available with an explicit label. An old successful task retains its original timestamp; a new task attempt is needed to describe a current observed outcome.

Pure deterministic fixture tasks can reuse a prior result when their complete declared dependencies, task specification, and scope remain equivalent. The method is labeled `reused_historical`, the original time is retained, and usage counts show executed versus reused attempts. Real browser tasks conservatively rerun on every recheck; the first release does not infer a website's complete dependencies from its URL.

HTTP collection resolves and validates the destination at connection time and connects to a numeric address while retaining the original HTTP host, TLS server name, and certificate checks. Browser launches pin the declared host mappings, deny unmatched names, block WebSockets, and enforce request/action scope. These controls apply to the owned test-browser process, not the operator's signed-in browser or system configuration. Context isolation and these controls do not establish a general-purpose browser sandbox.

## Specialist roles

| Role | Responsibility |
| --- | --- |
| Requirements researcher | Prioritize planning and source-review items from the operator's scoped brief. |
| Task actors | Deterministically execute declared steps in separate browser sessions and record exact observations; no model retelling is requested. |
| Offer/support analyst | Prioritize canonical items for recorded comparisons, documents and observed checkpoints. |
| Evidence reviewer | Prioritize recorded outcomes and follow-ups within scope; artifact metadata alone is not visual inspection. |
| Report writer | Arrange canonical decision explanations and coverage limits without changing wording or outcomes. |

The local coordinator owns time, action/call limits, allowed URLs, stage progress, and failure records. Role separation is an organization of work, not evidence of statistical independence.

With `--live-model`, four review roles call the configured provider. Browser task execution stays deterministic. Model output selects IDs from a canonical review catalog; the application validates required coverage, context digests and evidence bindings, then renders the exact recorded fits and safe follow-ups. No free-form model summary can override them. All legacy model prose remains in original JSON bundles and is excluded from newly rendered reports with an explicit notice. See [commentary consistency](commentary-consistency.md).

## Storage

A run directory contains `bundle.json`, local artifacts, and role reports. The fictional demo contains separate A/B/C/footer run directories and a summary/index. Source observations, artifact integrity, and live freshness remain different concepts.

Do not reuse personal browser profiles. Keep API keys, cookies, and private run outputs outside version control. A local `.env.live` and `runs/` directory are ignored; never force-add them. Review a bundle before sharing it.

## Hosting

The `site/` directory is a buildless static demonstration. It can be served with an ordinary HTTP server and deployed on Vercel using `vercel.json`. Its model-free example uses generated CLI data. The Python runner executes on the operator's machine; no server-side AI service is implied by the website.
