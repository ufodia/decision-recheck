"""Render the local launch artwork; never publish or use an authenticated profile."""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    artwork = root / "marketing" / "launch-preview.html"
    output = root / "marketing" / "images"
    output.mkdir(parents=True, exist_ok=True)
    channel = os.environ.get("DRC_BROWSER_CHANNEL", "chromium")
    if channel not in {"chromium", "chrome", "msedge"}:
        raise ValueError("Choose chromium, chrome, or msedge explicitly")
    names = ("01-product-change", "02-copy-and-fit", "03-inspect-the-evidence")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1700}, device_scale_factor=1)
        context.route("http://**/*", lambda route: route.abort())
        context.route("https://**/*", lambda route: route.abort())
        page = context.new_page()
        page.goto(artwork.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        for index, name in enumerate(names, 1):
            panel = page.locator(f"#slide-{index}")
            dimensions = panel.bounding_box()
            if not dimensions or dimensions["width"] != 1200 or dimensions["height"] != 1500:
                raise RuntimeError(f"Unexpected dimensions for {name}: {dimensions}")
            clipped = panel.evaluate("""el => [...el.querySelectorAll('[data-safe]')].filter(item => {
              const a = el.getBoundingClientRect(), b = item.getBoundingClientRect();
              return b.left < a.left + 48 || b.right > a.right - 48 ||
                     b.top < a.top + 40 || b.bottom > a.bottom - 40;
            }).map(item => item.textContent.trim())""")
            if clipped:
                raise RuntimeError(f"Artwork exceeds safe margins: {clipped}")
            panel.screenshot(path=str(output / f"{name}.png"))
            print(f"Rendered {name}.png (1200 x 1500)")
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
