"""Capture the real local fixture UI for documentation, using an explicit browser channel."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


def capture(url: str, destination: Path) -> None:
    parsed = urlsplit(url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.scheme != "http":
        raise ValueError("Documentation captures require a local preview URL")
    channel = os.environ.get("DRC_BROWSER_CHANNEL", "chromium")
    if channel not in {"chromium", "chrome", "msedge"}:
        raise ValueError("Unsupported browser channel")
    destination.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.goto(url, wait_until="networkidle")
        page.locator("#snapshot-B").click()
        page.locator("#report-content").get_by_text("Loading", exact=False).wait_for(state="hidden")
        for role in ("owner", "buyer", "marketing"):
            page.locator("#role-" + role).click()
            page.locator("#snapshot-panel").screenshot(path=str(destination / ("demo-" + role + ".png")))
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:4173")
    parser.add_argument("--output", type=Path, default=Path("assets"))
    args = parser.parse_args()
    capture(args.url, args.output)
