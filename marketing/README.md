# Decision Recheck launch kit

English launch materials for the public repository and demo. All product examples in the three artwork panels are fictional and follow the checked demo case. The artwork is explanatory illustration, not a screenshot or a claim of customer results.

## Ready to use

- `linkedin-post.txt`: the primary launch caption, under 3,000 characters.
- `buy-me-a-coffee-post.md`: the detailed project introduction.
- `buymeacoffee-post.html`: the same article body with semantic headings, lists, and links for a rich-text editor.
- `launch-manifest.json`: separate article title, content paths, intended audience, and image order; publication remains pending until read back from the platform.
- `sponsor-description.txt`: a concise support description without promised benefits or invented sponsorship tiers.
- `launch-preview.html`: editable, self-contained source and visual preview for all three images.
- `images/01-product-change.png`, `02-copy-and-fit.png`, `03-inspect-the-evidence.png`: upload in that order.
- `image-descriptions.json`: accessible descriptions for each image.

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

The first image states the problem and the changed offer. The second separates corrected copy from failed buyer fit. The third explains how the evidence can be inspected and gives the project links. Ivory paper, forest green, citrus highlights, large serif headlines, ruled sections, and restrained data typography extend the live demo's identity.

No customer, performance, provider-compatibility, test-count, or revenue claim is embedded in the artwork. Scheduling and publication status must be recorded separately after the platform confirms them; this directory alone is not proof of publication.

Copyright © 2026 ufodia. MIT license; see the repository LICENSE.
