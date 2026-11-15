"""Actual mutable HTTP sources, redirects, missing fields and partial-run recovery."""
from __future__ import annotations
from copy import deepcopy
import hashlib
from pathlib import Path
from decision_recheck.engine import run_case
from decision_recheck.validate import validate_bundle
from test_saas_scenarios import brief_for, buyer_fit


def live_brief(server):
    brief = brief_for()
    source = brief["sources"][0]
    source.pop("inline")
    source["url"] = server.base_url + "/offer.json"
    brief["permissions"]["allowed_hosts"] = ["127.0.0.1"]
    brief["permissions"]["allow_private_network"] = True
    return brief


def source_value(value=9, footer="Original footer"):
    return {"value": value, "plan": "Starter", "currency": "USD", "footer": footer}


def test_live_change_is_refetched_while_baseline_archive_remains_unchanged(tmp_path, local_sources):
    local_sources.json("/offer.json", source_value(9))
    brief = live_brief(local_sources)
    before_dir = tmp_path / "before"
    before = run_case(brief, before_dir)
    assert buyer_fit(before) == "meets"
    archive_path = before_dir / before["artifacts"][0]["path"]
    original_bytes = archive_path.read_bytes()
    requests_before = len(local_sources.requests)
    local_sources.json("/offer.json", source_value(49))
    after_dir = tmp_path / "after"
    after = run_case(brief, after_dir, baseline=before_dir / "bundle.json")
    assert len(local_sources.requests) > requests_before, "Recheck must contact the current source"
    assert archive_path.read_bytes() == original_bytes, "Recheck must preserve historical evidence"
    assert buyer_fit(after) == "fails", "Unchanged archive bytes cannot hide a changed live price"
    assert validate_bundle(after_dir / "bundle.json") == []
    assert {method for method, _path in local_sources.requests} == {"GET"}


def test_live_footer_only_edit_keeps_requirement_fit(tmp_path, local_sources):
    local_sources.json("/offer.json", source_value())
    brief = live_brief(local_sources)
    before_dir = tmp_path / "before"
    before = run_case(brief, before_dir)
    local_sources.json("/offer.json", source_value(footer="A harmless new legal footer"))
    after = run_case(brief, tmp_path / "after", baseline=before_dir / "bundle.json")
    assert buyer_fit(before) == buyer_fit(after) == "meets"


def test_inaccessible_current_source_is_unknown_not_a_failed_requirement(tmp_path, local_sources):
    local_sources.json("/offer.json", source_value())
    brief = live_brief(local_sources)
    before_dir = tmp_path / "before"
    run_case(brief, before_dir)
    local_sources.json("/offer.json", {"message": "Authentication required"}, status=401)
    after = run_case(brief, tmp_path / "after", baseline=before_dir / "bundle.json")
    assert buyer_fit(after) in {"conditional", "inconclusive"}
    assert buyer_fit(after) != "fails"


def test_missing_selected_live_field_is_unknown(tmp_path, local_sources):
    local_sources.json("/offer.json", {"plan": "Starter", "currency": "USD"})
    bundle = run_case(live_brief(local_sources), tmp_path / "run")
    assert buyer_fit(bundle) in {"conditional", "inconclusive"}


def test_redirect_cannot_expand_the_approved_hostname(tmp_path, local_sources):
    port = local_sources.base_url.rsplit(":", 1)[1]
    local_sources.redirect("/offer.json", f"http://localhost:{port}/restricted.json")
    local_sources.json("/restricted.json", source_value())
    bundle = run_case(live_brief(local_sources), tmp_path / "run")
    assert buyer_fit(bundle) in {"conditional", "inconclusive"}
    assert ("GET", "/restricted.json") not in local_sources.requests


def test_oversized_response_is_not_trusted_as_complete_evidence(tmp_path, local_sources):
    local_sources.json("/offer.json", {**source_value(), "filler": "x" * 10000})
    brief = live_brief(local_sources)
    brief["limits"]["max_response_bytes"] = 128
    bundle = run_case(brief, tmp_path / "run")
    assert buyer_fit(bundle) in {"conditional", "inconclusive"}


def test_zero_deadline_prevents_collection_and_leaves_a_partial_report(tmp_path, local_sources):
    local_sources.json("/offer.json", source_value())
    brief = live_brief(local_sources)
    brief["limits"]["timeout_seconds"] = 0
    output = tmp_path / "run"
    bundle = run_case(brief, output)
    assert buyer_fit(bundle) in {"conditional", "inconclusive"}
    assert not local_sources.requests
    assert (output / "bundle.json").exists()
    assert list(output.glob("*.html")), "Deadline interruption should still leave a readable report"
