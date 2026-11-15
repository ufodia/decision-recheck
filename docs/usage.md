# Usage and setup

## Restore a checkout

Install Python 3.12 and uv, clone this repository, and run `uv sync --locked`. For browser work run `uv run playwright install --no-shell chromium`. The runner uses the full bundled Chromium channel in headless mode. Initial installation requires network access; ordinary fictional demo generation makes no model or network calls.

You may explicitly select an already installed Chrome or Edge with `DRC_BROWSER_CHANNEL=chrome` or `DRC_BROWSER_CHANNEL=msedge`. There is no silent fallback. Every task still uses a separate temporary browser context, without attaching to your signed-in browser. Windows verification for this release uses the installed Chrome channel.

On a machine using an organization-managed certificate chain, preserve TLS verification and use the documented system CA support in the installed Node runtime if needed. Never disable certificate verification to download a browser.

## Commands

| Command | Purpose |
| --- | --- |
| `demo --output DIR` | Generate A/B/C/footer fictional cases, reports, and a summary. |
| `init --output FILE` | Write an editable fictional example brief. |
| `run --brief FILE --output DIR` | Capture a scoped review with optional `--live-model` proposals. |
| `recheck --baseline DIR --brief FILE --output DIR` | Recheck a validated prior bundle against the supplied current brief. |
| `report --bundle DIR --view owner --output FILE` | Produce a historical view of a validated bundle. Keep the output inside that bundle directory so artifact links remain valid. |
| `validate --bundle DIR` | Check versioned record shapes, references, artifact locations, sizes, and hashes. |

Prefix commands with `uv run decision-recheck`. Output directories must be new or empty. Existing evidence is preserved; choose a new directory for another run. A baseline must belong to the same case. The `report` command does not silently make a historical bundle current.

## Brief contract

Start with the generated brief or `examples/brief.example.json`. The top-level record includes `schema_version`, `case_id`, `title`, `product`, `scope`, `permissions`, `limits`, `sources`, `requirements`, `claims`, and `tasks`.

- **Scope:** identify the selected plan, locale, currency, billing period, and tax basis. Normalize commercial units before interpreting price fit.
- **Sources:** use exactly one of an explicit URL or supplied inline content. JSON field paths, whole text, and approved HTML selectors describe the scoped values being compared. HTML extraction requires the browser.
- **Requirements:** reference a declared source and selected field; choose `eq`, `lte`, `gte`, or `contains`. Supply the expected value and whether the condition is hard. Review inferred criteria before execution.
- **Claims:** link a supplied claim's source/field to a declared product/document source/field. A documentary match remains documentary evidence.
- **Tasks:** use fixed allowed actions and explicit assertions. A synthetic fixture task is labeled as such. A real browser task must have an allowed URL and a meaningful assertion; a blocked or untested attempt cannot establish capability absence.

Permissions default to read-only public requests. Explicit test-network access is needed for loopback/private fixtures. Interactive actions need a designated synthetic test environment and an explicit allowance. The operator is responsible for permission to inspect the target.

## Resource caps

Each snapshot accepts at most eight sources, five requirements, ten claims, and three task attempts. The runner caps browser actions and model calls; further token, response-size, and time limits can reduce work. Fixed browser actions do not grant permission to purchases, account administration, support messages, or arbitrary code.

Keep missing sources, authentication, CAPTCHA, timeouts, canceled work, and exhausted budgets visible in the partial report. Do not turn these into a completed audit or a failed product verdict.

Real browser task recipes rerun during a recheck. Only the built-in pure fixture tasks can reuse a validated unchanged result; the report labels this historical reuse and preserves its original time. A changed task specification or scope forces a fresh fixture attempt.

## Serve the public demo locally

Regenerate its fictional data with `uv run python scripts/export_demo.py`. Serve only the public directory with `uv run python -m http.server 8765 --directory site`, then visit `http://127.0.0.1:8765`. Stop the server when finished.

The demo includes inspectable artifacts and a ZIP of the fixture bundles. A locally imported JSON preview does not validate missing artifact files or establish source truth; use the CLI validator with the complete bundle for integrity checks.
