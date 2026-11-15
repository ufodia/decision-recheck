# Decision Recheck: when the product changes, recheck the decision

A price changes. A feature moves to another plan. The advertisement, support answer, and buying recommendation still describe yesterday's product.

**Decision Recheck** is my open-source SaaS audit pack for finding those disagreements, tracing them to evidence, and revisiting the decision when the product changes.

The latest version adds four optional live LLM review roles with a strict boundary: **the model can prioritize review items; it cannot rewrite the recorded decision.**

[Explore the interactive demo](https://decision-recheck.vercel.app/) · [Read the source on GitHub](https://github.com/ufodia/decision-recheck)

## One change. Three decisions to revisit.

The demonstration follows a **fictional** product and buyer:

- Starter originally costs **$9/month**, including CSV export.
- Starter rises to **$29/month**; CSV export moves to **$49/month Pro**.
- The advertisement and help answer still promise the original offer.
- The buyer's monthly budget remains **$20**.

A product owner needs the mismatch reproduced. A buyer needs to know whether the plan still fits. Marketing and support need to identify statements that no longer match the evidence.

Correcting the advertisement and help answer resolves the copy mismatch, but the buyer's budget failure remains. A better paragraph cannot make an unaffordable plan affordable.

Decision Recheck preserves that distinction across three audience reports connected to the same scoped evidence bundle.

## Four roles, with clear responsibilities

Optional live model review uses your configured provider. Each run requests four roles:

1. **Requirements researcher** selects source-review planning priorities before task execution.
2. **Offer and support analyst** prioritizes recorded comparison items and permitted follow-ups after evaluation.
3. **Evidence reviewer** prioritizes recorded decisions, scope limits, and follow-ups within the supplied evidence.
4. **Report writer** arranges application-owned decision explanations for the final review.

The browser task actor executes declared checks deterministically. It records what happened without asking a model to invent the outcome. Four model roles and three audience reports serve different purposes; they are not independent confirmations of a claim.

## Keep the decision attached to its evidence

Unrestricted prose can introduce a subtle contradiction: a recorded failure becomes “ready with exceptions,” or an unmet requirement becomes a recommendation to rewrite an inconvenient fact.

Each model now receives a finite catalog of application-defined review items and returns **only selected item IDs**. The application validates those selections and renders the wording from current evidence records.

- Required decisions and evidence preconditions cannot be omitted.
- Unknown or duplicate IDs, extra prose, replacement verdicts, stale context, and mismatched evidence references are rejected.
- A recorded **fails** outcome stays **fails** in the review.
- Factual documentation changes require **verification of the underlying behavior first**. A preferred buyer outcome is not evidence that a documented fact is wrong.

A rejected response leaves visible partial work, without silent repair, hidden retry, or provider fallback. Human review still matters: consistent reporting does not prove that a source is true or that the operator chose the right requirements.

## Tested with fresh responses on a real website

On **November 15, 2026**, I tested the current contract against the public **HTTPX Introduction and QuickStart documentation**, using OpenAI **gpt-4.1-mini**.

The completed baseline and recheck received **eight distinct new provider responses: four per run**. No recorded response was replayed or substituted. The recheck also reran a read-only browser task with three text assertions.

The case included positive, negative, and unknown outcomes. Three requirements were supported by the selected evidence. An intentionally incompatible requirement for documentation stating “no default timeout” failed. A two-hour support SLA remained inconclusive within those selected pages. The reports retained those outcomes and the instruction to verify behavior before changing factual documentation.

These checks examined documentation; they did not execute the HTTPX library, measure its runtime timeout, or test a support service. The models selected the required catalog items, demonstrating contract compliance rather than novel insights or independent corroboration.

An earlier strict attempt rejected two invalid selections and remained partial. After the request clarified the mandatory IDs, both completed runs passed the unchanged validation boundary. The full local suite also passed **335 tests, with zero skipped**.

Read the [live validation record and its limits](https://github.com/ufodia/decision-recheck/blob/main/docs/commentary-live-validation-2026-11-15.md) and the [decision-consistency contract](https://github.com/ufodia/decision-recheck/blob/main/docs/commentary-consistency.md).

## Try the evidence before connecting a model

The [public demo](https://decision-recheck.vercel.app/) is a static, fictional walkthrough requiring **no account, API key, or paid inference**. Compare **Changed offer** with **Corrected copy**, open the three report views, and follow the evidence links.

Real website checks and optional live LLM calls run through the local Python runner. You define the scope, sources, requirements, task checks, provider, and limits. Live provider use may incur charges. Models receive selected structured evidence and citation metadata, not full raw files or screenshot pixels.

The runner produces portable HTML reports and JSON bundles, supports an explicit baseline and recheck, and exposes blocked or uncertain work. FreshCtx supplies dependency and freshness mechanisms; Playwright supplies browser checks. The [README](https://github.com/ufodia/decision-recheck#run-the-demo) covers setup and usage.

## Help make the next decision easier to review

Try a case, [star the repository](https://github.com/ufodia/decision-recheck), or contribute a small reproduction: a feature moving between plans, a stale help answer, or a false positive. The project does not predict conversion, purchase probability, or market demand from simulated users.

If this work saves you review time, [buy me a coffee](https://buymeacoffee.com/ufodia). Support helps maintain reproducible cases, browser compatibility, regression checks, and clear documentation.

Built and maintained by **ufodia**. The core and model-free demo remain open source under the **MIT license**.
