# Decision Recheck: when the product changes, recheck the decision

A pricing page changes. A feature moves to another plan. The campaign, help answer, and buying recommendation still describe the old offer.

Decision Recheck is my open-source SaaS audit pack for making those disagreements visible and reviewable.

[Explore the interactive demo](https://decision-recheck.vercel.app/) · [Read the source on GitHub](https://github.com/ufodia/decision-recheck)

## A small case with three different consequences

The included demonstration uses a **fictional** product and buyer:

- Starter originally costs **$9/month** and includes CSV export.
- Starter changes to **$29/month**, while CSV export moves to **$49/month Pro**.
- The advertisement and support answer still describe the original offer.
- The buyer's monthly budget remains **$20**.

That change creates different questions for different people. A product owner needs a reproducible mismatch. A buyer needs to understand whether the product still meets their requirements. Marketing and support need to revisit statements that no longer agree with the product evidence.

The demo also includes a corrected-copy snapshot. The advertisement and help answer are repaired, but the buyer's budget failure remains. Fixing one problem must not silently erase another.

## What you can use today

Decision Recheck runs locally and produces portable HTML reports and JSON evidence bundles. A case connects explicit requirements, scoped sources, permitted task checks, captured artifacts, and findings.

You can:

- Review the same evidence from **product owner**, **buyer/user**, and **marketing/support** perspectives.
- Follow a finding to its supporting local artifacts and inspect its scope.
- Save a baseline and explicitly recheck after the source or offer changes.
- See blocked, untested, and uncertain work without turning missing access into a negative feature claim.
- Validate bundle references and artifact integrity before sharing a report.

The fictional demo requires **no API key or paid inference**. Optional model roles can propose structured interpretations for human review. FreshCtx provides the dependency and freshness mechanisms; Playwright supplies the browser checks. Their work is credited in the repository.

## Try it in a few minutes

Open the [demo workbench](https://decision-recheck.vercel.app/), choose **Changed offer**, then compare the three audience reports. Switch to **Corrected copy** and look at what changes—and what still fails.

For a local run, the [README](https://github.com/ufodia/decision-recheck#run-the-demo) covers Python 3.12, dependency setup, the CLI, and your first brief. Start with the fictional case before adapting a brief to an application you are authorized to test.

## What this first version does not claim

The public website displays fictional local results; it does not run an audit service or hold a server-side model key. A real case needs an operator-defined scope, sources, and task checks.

An automated task result does not establish human usability. Fresh evidence does not guarantee a correct interpretation. The project does not predict conversion, purchase probability, revenue, or market demand from simulated users. Paid-provider inference is separate from the included fixture validation.

## Help shape the next useful case

A small, reproducible example is especially valuable: a feature moving between plans, a stale support answer, a currency/billing mismatch, or a false positive the current rules should handle better. The repository includes contribution guidance and a security policy.

If Decision Recheck saves you review time, [star the repository](https://github.com/ufodia/decision-recheck), try a case, or share a useful issue. If you would like to support the work financially, [buy me a coffee](https://buymeacoffee.com/ufodia). Support helps me maintain reproducible fixtures, browser compatibility, and clear documentation.

The core and model-free demo remain open source under the MIT license.

Built and maintained by **ufodia**.
