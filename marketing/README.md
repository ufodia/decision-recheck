# Decision Recheck launch kit

English launch materials for the public repository and demo. The artwork illustrates the review workflow and a dated real HTTPX documentation test; it is not a screenshot or a claim of customer results. The public demo itself is fictional.

## Publication record

Verified on November 15, 2026:

- **LinkedIn:** the replacement post is scheduled for November 16, 2026 at 18:00 Europe/Istanbul, first in the queue. Its updated caption, three new images and custom alt text were read back. The original scheduled post was deleted with the owner's approval after LinkedIn did not persist its edited images. The replacement is scheduled, not yet published; no public post URL is available.
- **Buy Me a Coffee:** [the public project introduction is live](https://buymeacoffee.com/ufodia/decision-recheck-product-changes-recheck-decision), with its original artwork and the Open-source tools category. The existing article was updated and read back on November 15 with the four optional local model roles, application-rendered decision consistency, and the fresh baseline/recheck validation (four new responses per run). It links the dated 335-test record and explains the HTTPX documentation-only scope, the static demo, and local provider use. Its title, permalink, artwork, public visibility, and category were preserved. Follower email delivery was disabled at publication; this edit used Save changes without requesting an email.
- **GitHub:** the project is featured in [ufodia's profile](https://github.com/ufodia), and the repository's Sponsor button points to Buy Me a Coffee through `.github/FUNDING.yml`.

The recorded queue position is a point-in-time observation. No sponsorship campaign, membership tier, price, or sponsor outreach was changed.

## Launch materials

- `linkedin-post.txt`: the primary launch caption, under 3,000 characters.
- `buy-me-a-coffee-post.md`: the detailed project introduction.
- `buymeacoffee-post.html`: the same article body with semantic headings, lists, and links for a rich-text editor.
- `launch-manifest.json`: article title, content paths, audience, image order, and verified scheduling/publication details.
- `sponsor-description.txt`: a concise support description without promised benefits or invented sponsorship tiers.
- `launch-preview.html`: editable, self-contained source and visual preview for all three images.
- `images/01-product-change.png`, `02-copy-and-fit.png`, `03-inspect-the-evidence.png`: upload in that order.
- `image-descriptions.json`: accessible descriptions for the new images; `previous-image-descriptions.json` records the original scheduled panels.
- `images/buymeacoffee-cover.png` and `images/previous-*.png`: preserve the original published cover and scheduled LinkedIn panels.

The caption contains direct project links so a scheduled post remains useful without a later comment. It does not claim an algorithmic advantage, guaranteed reach, or a particular engagement outcome.

## Reproduce the images

From the repository root, after `uv sync --locked`, use an installed Chrome explicitly on Windows:

```powershell
$env:DRC_BROWSER_CHANNEL = 'chrome'
uv run python scripts/render_launch.py
```

Alternatively install Playwright Chromium and use its explicit channel:

```sh
uv run playwright install --no-shell chromium
DRC_BROWSER_CHANNEL=chromium uv run python scripts/render_launch.py
```

The script opens only the local artwork file in a temporary browser context. It renders three 1200 × 1500 PNGs and checks the designed content bounds. It does not contact LinkedIn, publish posts, or access an authenticated browser session. Segoe UI and Georgia are the intended Windows fonts; fallbacks are included for other hosts, whose typography may differ.

## Editorial direction

The new first panel explains the four model roles; the second illustrates the decision-consistency boundary; the third presents the scoped HTTPX live-model validation. Ivory paper, forest green, citrus highlights, large serif headlines, ruled sections, and restrained data typography extend the live demo's identity.

The live-test panel records the dated eight fresh model responses and 335-test local suite with its scope. Scheduling and publication status must be recorded separately after the platform confirms them; this directory alone is not proof of publication.

Copyright © 2026 ufodia. MIT license; see the repository LICENSE.
