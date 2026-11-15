"""Independent acceptance cases found during the end-to-end audit."""
from __future__ import annotations

import json
import pytest

from decision_recheck.engine import run_case
from decision_recheck.models import BriefError, load_brief
from decision_recheck.validate import validate_bundle
from helpers import brief_for
from test_cli import cli


def owner_fit(bundle):
    return next(d["fit"] for d in bundle["decisions"] if d["audience"] == "owner")


def test_owner_cannot_approve_when_a_requirement_is_unknown(tmp_path):
    brief = brief_for()
    brief["requirements"][0]["field"] = "missing"
    brief["claims"] = [{"id": "supported-copy", "source_id": "offer", "field": "plan", "actual_source_id": "offer", "actual_field": "plan"}]
    bundle = run_case(brief, tmp_path / "run")
    assert owner_fit(bundle) == "inconclusive"


def test_owner_uses_positive_requirement_evidence_without_needing_an_ad_claim(tmp_path):
    bundle = run_case(brief_for(), tmp_path / "run")
    assert owner_fit(bundle) == "meets"
    owner = next(d for d in bundle["decisions"] if d["audience"] == "owner")
    assert owner["evidence_ids"]


@pytest.mark.parametrize("bad_id", [7, None, [], {}])
def test_brief_record_ids_must_be_strings(bad_id):
    brief = brief_for()
    brief["sources"][0]["id"] = bad_id
    with pytest.raises(BriefError):
        load_brief(brief)


@pytest.mark.parametrize("value", ["", "   ", 7, None])
def test_browser_assertion_requires_meaningful_text(value):
    brief = brief_for()
    brief["tasks"] = [{"id": "browser-proof", "url": "https://example.com/", "steps": [{"action": "assert_text", "value": value}]}]
    with pytest.raises(BriefError, match="assert_text"):
        load_brief(brief)


@pytest.mark.parametrize("payload", [None, "unsupported fixture", 9, []])
def test_fixture_task_rejects_non_object_source_before_execution(payload):
    brief = brief_for()
    brief["sources"][0]["inline"] = payload
    brief["tasks"] = [{"id": "fixture-check", "method": "fixture", "source_id": "offer", "check": "plan"}]
    with pytest.raises(BriefError, match="inline object"):
        load_brief(brief)


def test_owner_retains_unresolved_price_units(tmp_path):
    brief = brief_for()
    brief["scope"].pop("currency")
    brief["sources"][0]["fields"]["price"] = "value"
    brief["requirements"][0]["field"] = "price"
    assert owner_fit(run_case(brief, tmp_path / "run")) == "conditional"


@pytest.mark.parametrize("check,payload", [("plan", {"price": {"amount": 9}}), ("help", {"text": ["Unexpected", "shape"]}), ("export", {"features": None})])
def test_invalid_fixture_fields_leave_unknown_coverage_instead_of_crashing(tmp_path, check, payload):
    brief = brief_for()
    brief["sources"].append({"id": "invalid-fixture", "inline": payload})
    brief["tasks"] = [{"id": "fixture-check", "method": "fixture", "source_id": "invalid-fixture", "check": check}]
    bundle = run_case(brief, tmp_path / "run")
    assert bundle["tasks"][0]["execution"] == "blocked"
    assert bundle["status"] == "partial"


@pytest.mark.parametrize("category", ["sources", "tasks", "findings", "decisions"])
@pytest.mark.parametrize("bad_id", [[], {}])
def test_unhashable_bundle_id_returns_validation_error(tmp_path, category, bad_id):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    bundle[category] = [{"id": bad_id}]
    (output / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    assert validate_bundle(output)


@pytest.mark.parametrize("field,value", [("scope", []), ("usage", []), ("changes", [None]), ("agent_proposals", [None])])
def test_malformed_rendered_bundle_containers_are_validation_errors(tmp_path, field, value):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    bundle[field] = value
    (output / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    result = cli("report", "--bundle", output, "--output", output / "historical.html")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_complete_cli_journey_rechecks_mutable_live_source(tmp_path, local_sources):
    path = tmp_path / "brief.json"
    assert cli("init", "--output", path).returncode == 0
    brief = brief_for()
    brief["sources"][0].pop("inline")
    brief["sources"][0]["url"] = local_sources.base_url + "/offer.json"
    brief["permissions"].update(allowed_hosts=["127.0.0.1"], allow_private_network=True)
    # Windows editors and older PowerShell commonly write a UTF-8 BOM.
    path.write_text(json.dumps(brief), encoding="utf-8-sig")
    local_sources.json("/offer.json", {"value": 9, "plan": "Starter", "currency": "USD"})
    baseline, changed = tmp_path / "baseline", tmp_path / "changed"
    result = cli("run", "--brief", path, "--output", baseline)
    assert result.returncode == 0, result.stderr
    assert cli("validate", "--bundle", baseline).returncode == 0
    assert cli("report", "--bundle", baseline, "--view", "buyer", "--output", baseline / "historical.html").returncode == 0
    old_bytes = (baseline / "bundle.json").read_bytes()
    local_sources.json("/offer.json", {"value": 49, "plan": "Starter", "currency": "USD"})
    result = cli("recheck", "--baseline", baseline, "--brief", path, "--output", changed)
    assert result.returncode == 0, result.stderr
    assert cli("validate", "--bundle", changed).returncode == 0
    after = json.loads((changed / "bundle.json").read_text(encoding="utf-8"))
    assert next(d["fit"] for d in after["decisions"] if d.get("requirement_id") == "criterion") == "fails"
    assert owner_fit(after) == "fails"
    assert (baseline / "bundle.json").read_bytes() == old_bytes
    assert all(method == "GET" for method, _ in local_sources.requests)
