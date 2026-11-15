"""A product task observation must affect the linked buying requirement."""
from __future__ import annotations
from decision_recheck.engine import run_case
from helpers import brief_for
from test_saas_scenarios import buyer_fit
from test_browser_boundaries import installed_browser


def task_brief(server):
    brief = brief_for("eq", True, True)
    brief["requirements"][0]["task_id"] = "export-task"
    brief["tasks"] = [{"id": "export-task", "title": "Perform CSV export", "url": server.base_url + "/export", "steps": [{"action": "assert_text", "selector": "#result", "value": "CSV exported"}]}]
    brief["permissions"].update({"allowed_hosts": ["127.0.0.1"], "allow_private_network": True})
    return brief


def test_observed_export_gate_overrides_a_documented_success(tmp_path, local_sources, installed_browser):
    local_sources.html("/export", '<div id="result">Upgrade to Pro to export</div>')
    bundle = run_case(task_brief(local_sources), tmp_path / "run")
    assert bundle["tasks"][0]["execution"] == "failed", bundle["tasks"]
    assert buyer_fit(bundle) == "fails"
    decision = next(d for d in bundle["decisions"] if d.get("requirement_id") == "criterion")
    assert any(e.startswith("task-") for e in decision["evidence_ids"])


def test_auth_blocked_task_keeps_documented_feature_unknown(tmp_path, local_sources, installed_browser):
    local_sources.html("/export", '<input type="password" id="field"><div id="result">Sign in to continue</div>')
    bundle = run_case(task_brief(local_sources), tmp_path / "run")
    assert bundle["tasks"][0]["execution"] == "blocked", bundle["tasks"]
    assert bundle["tasks"][0].get("error_type") == "PolicyError"
    assert buyer_fit(bundle) in {"inconclusive", "conditional"}


def test_linked_task_can_substantiate_documented_requirement(tmp_path, local_sources, installed_browser):
    local_sources.html("/export", '<div id="result">CSV exported successfully</div>')
    bundle = run_case(task_brief(local_sources), tmp_path / "run")
    assert bundle["tasks"][0]["execution"] == "passed", bundle["tasks"]
    assert buyer_fit(bundle) == "meets"
