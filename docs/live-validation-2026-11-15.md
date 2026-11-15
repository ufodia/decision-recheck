# Real-provider and public-site review — November 15, 2026

## What was exercised

The local CLI reviewed the actual public website at **https://decision-recheck.vercel.app/** and its public `robots.txt`, using isolated Chrome sessions and **OpenAI `gpt-4.1-mini`** through the real Chat Completions API. This was not a model simulation or a review of the fictional SaaS records embedded in the site's demonstration.

The site checks were restricted to public reads and three text assertions: the no-key demo statement, the fictional-demo boundary, and the loaded report heading. No account login, form submission, purchase, customer record, or private browser profile was used. The text model received selected source values and recorded events, not screenshot pixels or raw captured HTML.

## Observed provider runs

| Recorded run | Provider activity | Outcome |
| --- | --- | --- |
| A | Five attempted model requests; all connection failures; no returned proposal or provider usage | Partial review; the error was not presented as model success |
| B | Five accepted real-provider proposals; 9,943 reported tokens | The repeated source-validation bug exhausted the browser-action allowance and correctly prevented a CURRENT export |
| C | Five accepted real-provider proposals; 10,555 reported tokens | Complete / CURRENT, 24 browser actions, one executed task with three passed assertions, no warnings, valid bundle |

Across B and C the provider reported **20,498 tokens**. Dollar cost was not measured. Fifteen model-request attempts were made within the operator-approved bounds; no hidden retry or provider fallback was used. An authenticated model-catalog check also confirmed access to the selected model without running inference.

The baseline directory's full-file fingerprint remained unchanged across C. Source captures, task events and manifest hashes validated. Owner, buyer and marketing HTML views rendered without JavaScript errors or horizontal overflow.

## Findings checked against actual evidence

| Supplied requirement | Observed result | Basis |
| --- | --- | --- |
| Inspect the demonstration without an API key | Meets | Public statement and successful isolated, unauthenticated browser assertions |
| The hosted demonstration runs an AI model | Fails | The captured notice explicitly says the hosted page displays recorded fixtures and does not run an AI model |
| A two-hour support SLA is established | Inconclusive | The selected evidence does not establish this field; no global absence was inferred |
| Local setup documents Python 3.12 | Meets | Captured setup instructions |
| Robots identifies the canonical sitemap | Meets | Captured robots response |

The negative requirement was a deliberate comparison control. Its failure is a mismatch with the supplied requirement, not an undisclosed product defect. Overall owner fit was `fails`; marketing alignment remained `inconclusive` because no claim comparisons were declared. These deterministic results matched the independent source review.

## Bugs reproduced and corrected

- **Premature browser failure:** the runner compared a loading placeholder before the recorded report appeared. Assertions now wait within a bounded deadline; permanent mismatches still fail and missing targets remain incomplete.
- **Repeated baseline reads:** multiple prior decisions repeatedly read the same HTML source, exhausting the 36-action cap. A single baseline-comparison batch now shares a newly fetched observation and discards it before the independent final freshness check. Changed fields, unavailable sources and changes during final export remain covered by regressions.
- **Usage accounting:** final freshness reads were omitted from recorded action/time usage. Both successful and blocked exports now include them.
- **Provider compatibility and diagnostics:** modern completion-token limits are explicit, invalid/truncated responses retain reported usage, and diagnostics preserve useful status categories without provider message text or credentials.
- **Missing report content:** model recommendations were omitted from HTML. They are now available as unverified commentary with escaped content and evidence links.

## What the model got wrong

Valid JSON and valid evidence IDs did **not** establish factual accuracy. In C, the `task_actor` narration incorrectly said file-integrity verification happened in the browser; the selected source explicitly says the **CLI** verifies it. That narration also inferred offline behavior from text assertions and made an overly broad overall-fit claim. Prompt refinement alone did not eliminate these errors.

The default coordinator therefore no longer asks a model to retell deterministic browser execution. It records the actual steps directly and uses **four model review roles**. Newly rendered reports exclude legacy task narration with a visible explanation, while the original JSON remains unchanged. Other model prose is explicitly labeled unverified commentary, separate from requirement comparisons and task outcomes.

The other four C proposals preserved the main positive, negative and unknown results. Their prose still needs review: the preliminary researcher used loose documentary-confirmation wording, and some recommendations repeated disclosures already present. This is not a claim that every generated sentence is correct.

The removal of task narration and selection of the four remaining roles were verified using regressions and a replay of the recorded responses, without additional provider requests. **That replay is not new live inference.** Original A/B/C evidence was retained rather than rewritten to look correct.

## Limits and reproduction

This is one public-site case, not a model-quality benchmark, customer study, general autonomous browsing evaluation or universal provider-compatibility result. Local model-free generation, live-source capture, model commentary and fresh-source validation remain different operations. The Vercel website remains a static demonstration; no model key or remote audit backend was deployed there.

Use the [public-site walkthrough](live-site-review.md) and [checked-in brief](../examples/public-site-live.json) to reproduce the current four-role flow. Review expected values against the current site first. Raw artifacts remain outside Git because locally injected security-software URLs may contain machine-specific data; published verification records contain selected facts and aggregate outcomes only.
