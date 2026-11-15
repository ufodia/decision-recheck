# Contributing

Thank you for helping make product decisions easier to verify.

## Start with a reproducible case

The most useful contribution is small: an offer that changed, a task that exposed a contradiction, a clean control that should remain unaffected, or a false finding with its exact scope. Use fictional products and synthetic data. Do not submit customer records, credentials, private screenshots, copyrighted article dumps, or production account exports.

1. Open an issue describing the requirement, plan, locale, expected outcome, and observed outcome.
2. Include a minimal fixture or redacted evidence bundle and the CLI/version used.
3. Explain which result would demonstrate a fix.

## Development

Use Python 3.12 and `uv`. Restore with `uv sync --locked`, run `uv run python scripts/check.py`, then generate the offline demo with `uv run decision-recheck demo --output runs/demo`. Browser tests require `uv run playwright install --no-shell chromium` and any platform dependencies documented by Playwright. The runner uses the bundled Chromium channel in headless mode; explicitly select `DRC_BROWSER_CHANNEL=chrome` or `msedge` when testing with an installed browser.

Keep source changes focused and add a meaningful regression case. Tests must assert externally visible behavior rather than reproduce the implementation. Preserve the separate execution, evidence-support, freshness, fit, and human-review states.

Use short imperative commit summaries, such as `Handle unavailable pricing sources`. Pull requests should explain the problem, resulting behavior, and verification. Add dependency changes to both `pyproject.toml` and `uv.lock`.

## Evidence rules

- A stable archive is not proof that a live page is unchanged.
- A blocked task is not proof that a feature is missing.
- Vendor documentation and observed behavior must stay distinguishable.
- Several model responses citing one page remain one source.
- Fictional users cannot establish sales, customer demand, or advertising conversion.

The current first-party maintainer is **ufodia**. Contributions remain attributed to their actual authors. By submitting a contribution you agree to license your original work under this repository's MIT license.
