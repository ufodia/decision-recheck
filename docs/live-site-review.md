# Review an actual public website with model proposals

This walkthrough reviews the deployed Decision Recheck website itself: its public scope statements, installation instructions, rendered demo and robots file. The site is real; the SaaS records displayed inside its demo are fictional and are not treated as real vendor evidence.

The checked-in [brief](../examples/public-site-live.json) permits only reads and text assertions on `decision-recheck.vercel.app`. It does not attach to a signed-in browser, submit forms, purchase anything, or send messages. A text assertion confirms the observed text within the recorded attempt, not a general guarantee about the product.

## Configure the model privately

Create an ignored `.env.live` file in the repository root with these **setting names**. Supply your own key only in that local file:

```dotenv
DRC_MODEL_BASE_URL=https://api.openai.com/v1
DRC_MODEL_NAME=gpt-4.1-mini
DRC_MODEL_API_KEY=replace-with-your-private-key
DRC_MODEL_TOKEN_PARAMETER=max_completion_tokens
DRC_BROWSER_CHANNEL=chrome
```

Use `NAME=value` syntax, with one setting per line. Whole-line comments and matched single/double quotes are supported; shell expansion is not. Never paste a bare key, put one in a brief, or commit this file. The template value is not a working credential.

The explicit loader rejects invalid lines without reproducing their contents. `--no-env-file` prevents uv from independently parsing a credential file before that loader runs:

```sh
uv sync --locked
uv run --no-env-file python scripts/run_live_review.py --env-file .env.live --check-config
```

A successful configuration check performs **zero network/model calls**. It confirms local syntax and endpoint shape, not authentication, credit, model access or availability. Chrome must already be installed for this example; choose an explicitly supported installed channel or install bundled Chromium and set `DRC_BROWSER_CHANNEL=chromium`.

The [OpenAI model reference](https://developers.openai.com/api/docs/models/gpt-4.1-mini) lists Chat Completions support for this model. Current request-field semantics are documented in the [Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create). A valid account and provider billing/access are separate prerequisites.

## Run, inspect, then recheck

Use new output directories each time. These commands opt in to provider requests and may incur usage charges:

```sh
uv run --no-env-file python scripts/run_live_review.py --env-file .env.live --brief examples/public-site-live.json --output runs/public-live-A
uv run decision-recheck validate --bundle runs/public-live-A
```

Read `report-owner.html`, `report-buyer.html`, `report-marketing.html` and `bundle.json` in that output directory. A complete run should contain four model review proposals, one deterministic real-browser attempt, captured sources and linked artifacts. The task actor records actual events without asking a text model to retell them. A partial run remains usable for its recorded observations but is not a completed model review. The helper exits with code 3 for partial work and 2 for configuration/execution failure.

Only after checking the baseline, run one recheck:

```sh
uv run --no-env-file python scripts/run_live_review.py --env-file .env.live --brief examples/public-site-live.json --baseline runs/public-live-A --output runs/public-live-B
uv run decision-recheck validate --bundle runs/public-live-B
```

The brief caps each run at four requests, 600 output tokens per response, 80,000 conservative token reservations and 240 seconds. Two such runs permit at most eight requests. Reservations are not measured provider usage. No hidden retry occurs. A local/network/provider error can leave a role without a proposal; do not repeat a partial run without accounting for its attempted calls and reported usage.

For an additional historical rendering without a provider call:

```sh
uv run decision-recheck report --bundle runs/public-live-B --view buyer --output runs/public-live-B/buyer-historical.html
```

That file must say `HISTORICAL`: rendering saved evidence is not a fresh check. The original baseline files must remain unchanged, and real browser tasks must execute again during recheck.

## Compare conclusions with the source

These are the intended controls for the public page at the recorded review date. Check the current page before expecting the same outcomes; the website may change.

| Requirement | Expected interpretation | Evidence to inspect |
| --- | --- | --- |
| Inspect the demonstration without a key | Meets | Public key-free claim and recorded browser assertions, including the loaded example report |
| The hosted page itself runs an AI model | Fails, intentionally | The page explicitly says it displays recorded fixtures and does not run an AI model |
| A two-hour support SLA is established | Inconclusive | No SLA field is provided by the selected extractor; this does not prove that an SLA is absent everywhere |
| Local setup documents Python 3.12 | Meets | Captured setup text |
| Robots identifies the canonical sitemap | Meets | Captured public robots response |

The failed control expresses an intentionally incompatible requirement, not a defect in the static website. A correct recommendation explains that boundary or points to the local runner; it must not invent a hosted audit backend. No advertising claims are supplied, so the marketing summary must retain that coverage limit.

Check each model summary and recommendation against those observations. Evidence IDs must resolve, but a valid ID alone does not prove that a claim follows from the evidence. Missing support evidence must remain unknown, and the model must not present the embedded fictional SaaS as a real customer result. Model proposals cannot overwrite the deterministic requirement verdicts. Reports label generated prose as unverified model commentary; they do not certify its factual correctness. Legacy model-generated task narration is retained in the original JSON but excluded from newly rendered factual reports with an explicit notice.

## Keep evidence and credentials separate

The model receives selected source values, scope, task specifications/events and citation metadata. It does not receive screenshot pixels or full raw files. All model output remains a proposal for human review. Keep raw run artifacts private until reviewed: browsers or local security software can inject machine-specific URLs into otherwise public HTML. Do not publish raw traces, environment files, or provider exception text.

See [model access and privacy](model-and-privacy.md) and the dated [validation record](validation.md) for what was actually exercised and its limits.
