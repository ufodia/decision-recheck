# Usage and setup

## Restore a checkout

Install Python 3.12 and uv, clone this repository, and run `uv sync --locked`. For browser work run `uv run playwright install --no-shell chromium`. The runner uses the full bundled Chromium channel in headless mode. Initial installation requires network access; ordinary fictional demo generation makes no model or network calls.

You may explicitly select an already installed Chrome or Edge with `DRC_BROWSER_CHANNEL=chrome` or `DRC_BROWSER_CHANNEL=msedge`. There is no silent fallback. Every task still uses a separate temporary browser context, without attaching to your signed-in browser. Windows verification for this release uses the installed Chrome channel.

On a machine using an organization-managed certificate chain, preserve TLS verification and use the documented system CA support in the installed Node runtime if needed. Never disable certificate verification to download a browser.

With the skill installed in a separate case workspace, point uv at the runner checkout without changing directories. Use `uv sync --locked --project "<runner-checkout>"` once, then `uv run --locked --project "<runner-checkout>" decision-recheck --help`. Paths supplied to the runner resolve from the case workspace. The model-free demo requires no browser or provider configuration.

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

## Connect your own product

`init` produces a working **fictional** brief. It does not discover your product or infer browser steps. Make these edits before describing the result as a review of your application:

1. Set `case_id`, `title`, `product` and the commercial `scope`. Keep `case_id` stable across a baseline and its recheck.
2. Replace each relevant inline source with a permitted `url`. A source accepts **one** of `inline` or `url`, never both. Add the exact source and task hostnames to `permissions.allowed_hosts`.
3. Update source `fields` and the requirements and claims that refer to them. JSON sources use dotted paths such as `features.csv_export`; HTML sources use selectors that identify exactly one non-empty element.
4. Replace the built-in `method: "fixture"` tasks with explicit `method: "browser"` recipes for your application, or remove them and their `task_id` references for a document-only review. A fixture result is synthetic even when another source uses a real URL.
5. Install or explicitly select a browser if the brief uses HTML sources or browser tasks. Run a new baseline, validate its complete bundle, inspect each report, and only then run a recheck into a different directory.

For example, this is the shape of a **read-only browser task**. Replace the reserved example URL, selector and expected text with your own permitted test page. It checks visible text, not whether an export actually completed:

```json
{
  "id": "check-export-guidance",
  "title": "Check the export instructions",
  "method": "browser",
  "url": "https://your-product.example/help/export",
  "steps": [
    {
      "action": "assert_text",
      "selector": "main h1",
      "value": "Export your data"
    }
  ]
}
```

Use `allowed_hosts: ["your-product.example"]` and `allowed_actions: ["read", "assert_text"]` for that example. Add only other hosts the approved page actually needs; do not use a wildcard to avoid diagnosing blocked resources. Real browser attempts rerun on recheck.

Text assertions allow up to five seconds, bounded by the remaining run deadline, for delayed content to match. A permanent mismatch fails; a missing/disappearing target or an exhausted deadline remains incomplete. The outcome is specific to that recorded attempt.

**Choose matching value types.** JSON can provide numeric prices and boolean entitlements. HTML selector extraction returns text: `"$29 / month"` is not a numeric `29`, so `lte: 20` cannot establish a budget result from it. Use a numeric JSON field for numeric comparisons, or a text comparison for an explicitly textual requirement. Missing, incompatible or inaccessible values remain unknown.

**Understand the three different files.** A brief is an input specification. `bundle.json` is a captured run. A report is a readable view of that run. The website imports a bundle, not a brief; use `run --brief` to execute a brief and `validate --bundle` to check a complete captured bundle with its artifacts.

## Common setup and interpretation problems

| What you see | What it means and what to do |
| --- | --- |
| Existing output directory or report is refused | Choose a new output path. Preserve the old evidence for comparison. |
| Browser executable is missing | Install bundled Chromium, or explicitly set `DRC_BROWSER_CHANNEL` to the installed `chrome` or `msedge` channel. |
| Source or task is blocked | Inspect the brief's exact host/action scope, page access, selectors and browser setup. A blocked attempt does not prove that the product lacks the feature. |
| Budget fit is inconclusive | Check the selected source field, numeric type, currency and billing period before changing the requirement. |
| Corrected copy but buyer fit still fails | The marketing statement and the buyer's requirements are separate decisions; fixing a promise does not change the price or entitlement. |
| `validate` succeeds | The stored bundle's structure and artifact integrity passed; this is not a fresh observation of the live product. |
| The website says “Imported metadata” | No artifact verification or live source check happened in the browser. Run the CLI validator against the complete bundle. |

## Use the reports to decide

Open the reports in the bundle directory after running `validate`. Start from a named plan and pay attention to the source and task references on each decision.

- **Owner** — Decide which conflict warrants a product, task, or documentation follow-up. Reproduce the scoped mismatch and agree on the result that would close it. An unmet buyer criterion can be an expected plan limit.
- **Buyer** — Resolve failed or unknown required criteria before treating the plan as a fit. For example, a fictional $29/month offer does not meet a $20/month cap even when its help text is correct. If the extracted price is plain text, obtain an authoritative numeric price with the same currency, billing period, and tax basis.
- **Marketing/support** — Verify the recorded comparison before issuing a correction. A document match establishes agreement for the selected fields. If the support SLA field is missing, locate the governing term for that plan or leave the claim unresolved.

On recheck, distinguish changed source fields, changed task outcomes, and brief edits. A task outcome can affect a linked buyer requirement and the owner view while the marketing document comparison still agrees. Record altered requirements and scope explicitly when comparing runs.

Windows PowerShell browser selection:

```powershell
$env:DRC_BROWSER_CHANNEL = "chrome"
uv run decision-recheck run --brief brief.json --output runs/baseline-2
```

Linux/macOS shell selection:

```sh
DRC_BROWSER_CHANNEL=chrome uv run decision-recheck run --brief brief.json --output runs/baseline-2
```

These commands require a corresponding installed Chrome browser and a reviewed brief. Browser sessions are isolated from your normal signed-in profile.

## Resource caps

Each snapshot accepts at most eight sources, five requirements, ten claims, and three task attempts. The runner caps browser actions and model calls; further token, response-size, and time limits can reduce work. Fixed browser actions do not grant permission to purchases, account administration, support messages, or arbitrary code.

Keep missing sources, authentication, CAPTCHA, timeouts, canceled work, and exhausted budgets visible in the partial report. Do not turn these into a completed audit or a failed product verdict.

Real browser task recipes rerun during a recheck. Only the built-in pure fixture tasks can reuse a validated unchanged result; the report labels this historical reuse and preserves its original time. A changed task specification or scope forces a fresh fixture attempt.

Several old decisions may depend on the same source. Within one baseline-comparison batch, they share a newly fetched observation; that short-lived batch is discarded before the final export independently rechecks the live source. This does not reuse an archived page as current evidence. Reported usage includes the final validation reads.

## Serve the public demo locally

Regenerate its fictional data with `uv run python scripts/export_demo.py`. Serve only the public directory with `uv run python -m http.server 8765 --directory site`, then visit `http://127.0.0.1:8765`. Stop the server when finished.

The demo includes inspectable artifacts and a “Download complete example bundles” ZIP link below the workbench. Select **Plan changed**, switch between the three audiences, then select **Copy repaired** to see why corrected marketing and buyer fit can differ. The footer control compares a cosmetic-only change with the original baseline.

A locally imported JSON preview does not validate missing artifact files or establish source truth; use the CLI validator with the complete bundle for integrity checks. If the recorded example fails to load, use **Retry loading example**. An already imported local bundle remains available during the retry.
