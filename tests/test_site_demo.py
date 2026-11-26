"""Optional live static-demo smoke checks. Set DRC_DEMO_URL to an owned preview."""
from __future__ import annotations
from copy import deepcopy
import json
import os
from urllib.parse import urljoin
import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.fixture
def demo_page():
    base_url = os.environ.get("DRC_DEMO_URL")
    if not base_url: pytest.skip("Set DRC_DEMO_URL to test the served static demo")
    with sync_playwright() as p:
        channel = os.environ.get("DRC_BROWSER_CHANNEL", "chromium")
        browser = p.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(base_url, wait_until="domcontentloaded")
        assert response and response.ok
        expect(page.locator("#download-bundle")).to_be_enabled()
        expect(page.locator("#report-content .finding").first).to_be_visible()
        yield page, base_url, errors
        browser.close()
        assert errors == [], errors


def test_demo_snapshot_and_audience_views_use_actual_report_data(demo_page):
    page, base_url, errors = demo_page
    for snapshot in ("A", "B", "C", "footer"):
        page.locator(f'[data-snapshot="{snapshot}"]').click()
        expect(page.locator(f'[data-snapshot="{snapshot}"]')).to_have_attribute("aria-selected", "true")
        for role, label in (("owner", "Product owner"), ("buyer", "Buyer / user"), ("marketing", "Marketing / support")):
            page.locator(f'[data-role="{role}"]').click()
            expect(page.locator(".report-kicker")).to_contain_text(label)
            href = page.locator("#open-report").get_attribute("href")
            assert href == f"/data/{snapshot}/report-{role}.html"
            response = page.request.get(urljoin(base_url, href))
            assert response.ok, href
        for link in page.locator(".artifact-download").all():
            href = link.get_attribute("href")
            assert href.startswith(f"/data/{snapshot}/artifacts/")
            assert page.request.get(urljoin(base_url, href)).ok, href
    page.locator('[data-snapshot="B"]').click()
    page.locator('[data-role="buyer"]').click()
    expect(page.locator("#report-content")).to_contain_text("fails")
    expect(page.locator("#report-content")).to_contain_text("29")
    expect(page.locator(".report-statuses")).to_contain_text("Required")
    expect(page.locator(".finding-label").filter(has_text="Optional")).to_be_visible()
    expect(page.locator("#report-content")).to_contain_text("Treat this criterion as unmet for the checked plan.")
    page.set_viewport_size({"width": 375, "height": 812})
    assert page.evaluate("document.documentElement.scrollWidth") == 375
    page.locator('[data-snapshot="C"]').click()
    expect(page.locator("#report-content")).to_contain_text("fails")
    page.locator('[data-role="marketing"]').click()
    expect(page.locator("#report-content")).to_contain_text("Fit: meets")
    page.locator('[data-role="buyer"]').click()
    page.locator('[data-snapshot="footer"]').click()
    expect(page.locator("#report-content")).to_contain_text("meets")


def test_demo_tabs_support_keyboard_and_evidence_expansion(demo_page):
    page, _, _ = demo_page
    page.locator('[data-snapshot="A"]').focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator('[data-snapshot="B"]')).to_be_focused()
    expect(page.locator('[data-snapshot="B"]')).to_have_attribute("aria-selected", "true")
    page.keyboard.press("End")
    expect(page.locator('[data-snapshot="footer"]')).to_be_focused()
    page.keyboard.press("Home")
    expect(page.locator('[data-snapshot="A"]')).to_be_focused()
    page.locator('[data-role="owner"]').focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator('[data-role="buyer"]')).to_be_focused()
    link = page.locator(".finding-evidence a").first
    target = link.get_attribute("href")
    link.click()
    expect(page.locator(target)).to_have_attribute("open", "")


def test_demo_json_download_is_the_selected_generated_bundle(demo_page, tmp_path):
    page, _, _ = demo_page
    page.locator('[data-snapshot="B"]').click()
    with page.expect_download() as download_info:
        page.locator("#download-bundle").click()
    download = download_info.value
    assert download.suggested_filename == "decision-recheck-B.json"
    path = tmp_path / download.suggested_filename
    download.save_as(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["schema_version"] == "1.0"
    assert bundle["mode"] == "fixture"
    assert bundle["artifacts"] and bundle["decisions"]
    pricing = next(source for source in bundle["sources"] if source["id"] == "pricing")
    assert pricing["values"]["price"] == 29


def test_local_metadata_import_renders_untrusted_text_without_execution(demo_page):
    page, base_url, _ = demo_page
    catalog = page.request.get(urljoin(base_url, "/data/demo.json")).json()
    bundle = deepcopy(catalog["snapshots"][0]["bundle"])
    payload = '<img src=x onerror="window.__injected=true">'
    bundle["title"] = payload
    bundle["decisions"][0]["title"] = payload
    bundle["decisions"][0]["next_step"] = payload
    for source in bundle["sources"]:
        source["url"] = "https://should-not-fetch.invalid/private-source"
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.locator("#bundle-file").set_input_files({"name": "synthetic-untrusted.json", "mimeType": "application/json", "buffer": json.dumps(bundle).encode()})
    expect(page.locator("#demo-feedback")).to_contain_text("metadata preview")
    expect(page.locator("#case-title")).to_have_text(payload)
    page.locator('[data-role="buyer"]').click()
    expect(page.locator("#report-content")).to_contain_text(payload)
    assert page.locator('img[src="x"]').count() == 0
    assert page.evaluate("window.__injected === true") is False
    assert page.locator(".artifact-download").count() == 0
    expect(page.locator("#open-report")).to_be_hidden()
    assert not any("should-not-fetch.invalid" in url for url in requests), "Opening a local metadata bundle must not contact its supplied sources"
    page.locator('[data-snapshot="A"]').click()
    expect(page.locator("#open-report")).to_be_visible()


def test_invalid_and_oversized_import_preserve_working_fixture(demo_page):
    page, _, _ = demo_page
    page.locator("#bundle-file").set_input_files({"name": "broken.json", "mimeType": "application/json", "buffer": b'{"schema_version":'})
    expect(page.locator("#demo-feedback")).to_contain_text("Could not open")
    page.locator('[data-snapshot="B"]').click()
    expect(page.locator("#report-content .finding").first).to_be_visible()
    page.locator("#bundle-file").set_input_files({"name": "oversized.json", "mimeType": "application/json", "buffer": b"x" * (2 * 1024 * 1024 + 1)})
    expect(page.locator("#demo-feedback")).to_contain_text("smaller than 2 MB")
    page.locator('[data-role="buyer"]').click()
    expect(page.locator("#report-content")).to_contain_text("fails")


@pytest.fixture
def unloaded_demo_page():
    """Own a browser before navigation so initial network failures can be tested."""
    base_url = os.environ.get("DRC_DEMO_URL")
    if not base_url:
        pytest.skip("Set DRC_DEMO_URL to test the served static demo")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=os.environ.get("DRC_BROWSER_CHANNEL", "chromium"), headless=True)
        page = browser.new_page(accept_downloads=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        catalog = page.request.get(urljoin(base_url, "/data/demo.json")).json()
        yield page, base_url, catalog
        browser.close()
        assert errors == [], errors


def _import_example(page, catalog):
    bundle = deepcopy(catalog["snapshots"][0]["bundle"])
    bundle["title"] = "My retained local review"
    page.locator("#bundle-file").set_input_files({
        "name": "local-review.json", "mimeType": "application/json",
        "buffer": json.dumps(bundle).encode(),
    })
    expect(page.locator("#case-title")).to_have_text("My retained local review")
    return bundle


def test_missing_catalog_keeps_import_until_successful_retry(unloaded_demo_page):
    page, base_url, catalog = unloaded_demo_page
    def fail(route):
        route.fulfill(status=503, body="temporarily unavailable")
    page.route("**/data/demo.json", fail)
    page.goto(base_url)
    expect(page.locator("#retry-fixture")).to_be_visible()
    bundle = _import_example(page, catalog)
    page.locator('[data-snapshot="B"]').click()
    expect(page.locator("#case-title")).to_have_text(bundle["title"])
    expect(page.locator("#demo-feedback")).to_contain_text("local preview stays open")
    expect(page.locator("#open-report")).to_be_hidden()
    assert page.locator('[data-snapshot][aria-selected="true"]').count() == 0
    page.unroute("**/data/demo.json", fail)
    page.locator("#retry-fixture").click()
    expect(page.locator("#retry-fixture")).to_be_hidden()
    expect(page.locator("#case-title")).to_have_text(bundle["title"])
    page.locator('[data-snapshot="B"]').click()
    expect(page.locator('[data-snapshot="B"]')).to_have_attribute("aria-selected", "true")
    expect(page.locator("#case-title")).to_contain_text("within budget")
    expect(page.locator("#open-report")).to_have_attribute("href", "/data/B/report-owner.html")


def test_late_catalog_failure_does_not_replace_imported_status(unloaded_demo_page):
    page, base_url, catalog = unloaded_demo_page
    pending = []
    page.route("**/data/demo.json", lambda route: pending.append(route))
    page.goto(base_url, wait_until="domcontentloaded")
    bundle = _import_example(page, catalog)
    status = page.locator("#run-status").text_content()
    assert pending, "The catalog request must be outstanding for this regression"
    pending[0].fulfill(status=503, body="unavailable")
    expect(page.locator("#retry-fixture")).to_be_visible()
    expect(page.locator("#run-status")).to_have_text(status)
    expect(page.locator("#case-title")).to_have_text(bundle["title"])
    expect(page.locator("#download-bundle")).to_be_enabled()


def test_changed_offer_cta_remembers_selection_while_loading(unloaded_demo_page):
    page, base_url, catalog = unloaded_demo_page
    pending = []
    page.route("**/data/demo.json", lambda route: pending.append(route))
    page.goto(base_url, wait_until="domcontentloaded")
    page.locator("#explore-changed-offer").click()
    assert pending
    pending[0].fulfill(status=200, content_type="application/json", body=json.dumps(catalog))
    expect(page.locator('[data-snapshot="B"]')).to_have_attribute("aria-selected", "true")
    expect(page.locator("#open-report")).to_have_attribute("href", "/data/B/report-owner.html")
    expect(page.locator("#report-content")).to_contain_text("fails")
