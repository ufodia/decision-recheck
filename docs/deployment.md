# Deployment and recovery

Production demo: <https://decision-recheck.vercel.app/>

## Hosting contract

The project is a static Vercel site under the existing `milemori` team, project `decision-recheck`. `vercel.json` serves `site/` without a Python build, server-side model key, or remote audit backend. The Python audit runner remains a local tool.

Source, lockfile, original artwork, public fictional evidence, and deployment configuration are backed up on GitHub `main`. Restore them with `git clone` and `uv sync --locked`. Private run data, Vercel credentials, and local environment files are not part of the repository.

## Reproduce and publish a change

1. Review the source changes and run `uv run python scripts/check.py` with the explicit browser channel available on the host.
2. Regenerate fictional public results with `uv run python scripts/export_demo.py` when the audit behavior or fixtures change. Review the generated data before committing it.
3. Integrate the reviewed changes into GitHub `main` and verify the remote SHA. Deploy from that clean, checked source.
4. Use the official Vercel CLI with the operator's own account. If needed, complete `npx --yes vercel@65.16.0 login` personally.
5. Link with `npx --yes vercel@65.16.0 link --project decision-recheck --scope milemori --yes`, then deploy with `npx --yes vercel@65.16.0 deploy --prod --scope milemori --yes --json`.
6. Read back the READY state and production alias. Verify the public homepage, CSS, script, cover, demo JSON, all role reports, and artifact URLs without an authenticated bypass.

Vercel linking may create a local `.env.local` and `.vercel/` metadata. Keep both ignored and never publish their credential contents. Confirm that the deployment file list excludes them. Root artwork is excluded from upload while `site/assets/` remains included.

The initial publication uses explicit CLI deployments; automatic deployment on every Git push was not configured by this workflow.

## Search configuration

The homepage has a self-referencing production canonical and absolute social-preview URLs. The sitemap contains only the public homepage; update `lastmod` when that page has a meaningful content change.

`robots.txt` permits the homepage and rendering resources. It excludes the raw `/data/` fixture/report area while explicitly allowing `/data/demo.json`, which the workbench needs. These crawler rules do not restrict human access or guarantee deindexing of a linked URL.

Google ownership setup requires the authorized operator account and the exact verification filename/content shown by Search Console. Keep a verified ownership file in place. Do not copy an unrelated verification token or treat a public file alone as proof that ownership was verified.

After an authorized production update, read back ownership, submit the canonical production sitemap, inspect its processing status, and inspect the homepage. Record the actual indexing-request result; a request does not guarantee indexing. Preserve account sessions and handle sign-in or access prerequisites personally when required.
