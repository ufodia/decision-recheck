# Model access, costs, and privacy

## Execution modes

The fictional demo uses deterministic fixture checks and makes no model calls. Ordinary source/task execution can produce evidence-backed reports without live model proposals. Passing `--live-model` explicitly enables the configured role-proposal adapter.

The adapter uses an OpenAI-compatible HTTP `POST /chat/completions` contract with JSON responses. The default coordinator requires an ID-only canonical review selection; it does not accept free-form model conclusions for reports. Configuration is read from `DRC_MODEL_BASE_URL`, `DRC_MODEL_NAME`, and `DRC_MODEL_API_KEY`. The default base URL is `https://api.openai.com/v1`; choose a model that supports the required request shape. No model name is silently guessed, and provider fallback is not automatic.

Set variables in your shell. `.env.example` documents the names; the application does not automatically load `.env` files. Do not place a key in a brief, bundle, repository, or public website.

For an explicit local file, use `uv run --no-env-file python scripts/run_live_review.py --env-file .env.live --check-config`. This validates the file without a provider request and reports syntax errors without echoing input lines. Use `NAME=value` on each line; do not paste a bare API key. The file and all `.env.*` files other than `.env.example` are ignored by Git. See the [public-site walkthrough](live-site-review.md) for the complete run and recheck commands.

Requests use `max_completion_tokens` by default and cap each response at 600 output tokens. A compatible provider that requires the legacy field can explicitly set `DRC_MODEL_TOKEN_PARAMETER=max_tokens`. There is no automatic parameter retry, model substitution, or provider fallback. Reasoning models can consume this output allowance on non-visible reasoning; a truncated response is rejected rather than treated as a complete proposal. Choose a model whose request and response behavior fits this bounded adapter.

The response contract, role sequence, budgets, malformed JSON, and unsupported evidence references are tested using mock transport. Paid production inference is not part of the included fixture validation. Compatibility with every service describing itself as OpenAI-compatible is not claimed.

Live model testing is recorded separately from the fixture suite in the dated [validation record](validation.md). A proposal passing JSON and citation validation is not evidence that every sentence is factually correct. Check narrative claims against the scoped source and task observations.

## What gets sent

Live proposals receive the structured case/evidence content supplied by the coordinator. This can include product claims, selected page content, requirement values, and artifact identifiers. Review your inputs and provider's data-handling terms before using private data. The local runner does not make a cloud provider local.

Every model review role receives the product identity, case scope, captured source values, an artifact citation index and a canonical review catalog. It chooses the order of allowed review items; all recorded decision items and evidence preconditions are mandatory. The browser task actor executes its declared recipe and records observations deterministically. Full raw files and screenshot pixels are not sent to the text model; a citation to a screenshot does not mean the model visually inspected it. The application renders selected review points from the current bundle, including exact fits and behavior-verification preconditions.

The default response contains only `review_item_ids`. Extra prose, verdict replacements, unknown or duplicate selections, omitted mandatory items, stale catalog digests and forged evidence bindings are rejected. The low-level adapter retains legacy free-prose compatibility only when called without a catalog; the coordinator and report renderer do not publish that prose. No model output can add tools, expand allowed hosts, execute arbitrary code, or convert page text into permissions. See [decision-consistent review](commentary-consistency.md).

Successful responses may also record a provider response identifier, actual model snapshot, creation timestamp and per-role reported token total. These optional, bounded metadata fields are distinct from the configured model alias. They support run auditing; they do not authenticate a third-party bundle or prove that generated claims are correct. Missing metadata is omitted, not invented. No raw provider headers or response body are copied into these fields.

## Usage and limits

Configured model-call, token-reservation, action, response-size, and time limits constrain the run. Limits apply to the work actually performed; an exhausted or invalid proposal becomes visible partial work. Usage received from a provider is recorded separately from reservations. The application does not claim a measured dollar cost when current prices or provider usage are unavailable.

A live run requests one requirements proposal and three final review proposals: four calls if the budget permits, independently of the number of deterministic browser tasks. The public-site example has one task and a four-call cap. A baseline plus one recheck is at most eight calls, without hidden retries. Its explicit 80,000-token reservation budget is a conservative UTF-8-based upper allowance, not a measured usage or charge. The smaller default budget can intentionally leave larger cases partial. Provider-reported usage is retained even when a response has invalid JSON, unsupported evidence IDs, or a truncation/refusal result.

Earlier versions requested free-form summaries and `task_actor` narration. Real-provider reviews found incorrect or ambiguous conclusions, so task events are reported directly and the four review roles now select application-owned items. Newly rendered reports exclude all legacy free prose with a visible explanation and retain the original JSON unchanged. Selection priority remains a model proposal for human review; it cannot replace the recorded verdict or supply new recommendation wording.

Source mode and model mode are independent. Calling a model on fictional fixtures does not turn the fixtures into real customer or vendor evidence.

Blocked model stages include safe diagnostic categories, numeric HTTP/transport status and known provider error codes where available. Raw provider messages, headers and response bodies are deliberately omitted because they may contain credentials or private input. A connection failure and an account quota rejection require different remedies; neither becomes a fabricated model result.

No provider key is present in the static Vercel demo. It displays fictional evidence generated by the local CLI. Downloaded JSON and locally imported data remain in the visitor's browser; the website does not run a remote audit.

## Before sharing

Inspect raw screenshots, captured content, task events, and model proposals. Hashes protect integrity, not confidentiality or anonymization. Keep private run directories out of Git and redact sensitive information through a reviewed export process. Read [SECURITY.md](../SECURITY.md) before filing an issue.
