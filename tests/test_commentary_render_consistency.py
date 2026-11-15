"""Adversarial report-boundary checks; no model or external website requests."""
from copy import deepcopy
from html import escape
import json

import pytest

from decision_recheck.commentary import CONTRACT, catalog_digest, catalog_for_role, resolve_selection
from decision_recheck.demo import example_brief
from decision_recheck.engine import run_case
from decision_recheck.render import render_report
from decision_recheck.validate import validate_bundle


@pytest.fixture
def recorded_case(tmp_path):
    brief = example_brief("B")
    brief["claims"] = []
    brief["requirements"].append({
        "id": "support-sla", "label": "Selected evidence establishes a two-hour support SLA",
        "source_id": "pricing", "field": "support_response_sla",
        "operator": "eq", "expected": "2 hours", "hard": False,
    })
    root = tmp_path / "recorded"
    bundle = run_case(brief, root)
    return bundle, root


def proposal_for(bundle, role="report_writer"):
    catalog = catalog_for_role(bundle, role)
    return {
        "role": role,
        "review": "proposed",
        "commentary_contract": CONTRACT,
        "catalog_sha256": catalog_digest(bundle, role),
        "review_item_ids": [item["id"] for item in catalog],
        "evidence_ids": list(dict.fromkeys(ref for item in catalog for ref in item["evidence_ids"])),
    }


def store(bundle, root):
    (root / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")


def test_canonical_commentary_preserves_failed_owner_and_unknown_sla(recorded_case):
    bundle, root = recorded_case
    proposal = proposal_for(bundle)
    bundle["agent_proposals"] = [proposal]
    items = resolve_selection(bundle, proposal)
    owner = next(item for item in items if item.get("decision_id") == "decision-owner-alignment" and item.get("fit"))
    sla = next(item for item in items if item.get("decision_id") == "decision-buyer-support-sla" and item.get("fit"))
    assert owner["fit"] == "fails"
    assert sla["fit"] == "inconclusive"
    assert any(word in sla["text"].lower() for word in ("selected", "scoped", "captured"))
    for audience in ("owner", "buyer", "marketing"):
        html = render_report(bundle, audience)
        assert escape(owner["text"], quote=True) in html
        assert escape(sla["text"], quote=True) in html
        assert "ready with exceptions" not in html.lower()
    store(bundle, root)
    assert validate_bundle(root) == []


@pytest.mark.parametrize("role", ["requirements_researcher", "offer_support_analyst", "evidence_reviewer", "report_writer", "task_actor"])
def test_legacy_free_prose_cannot_override_rendered_decisions_or_modify_json(recorded_case, role):
    bundle, root = recorded_case
    bundle["agent_proposals"] = [{
        "role": role, "review": "proposed",
        "summary": "QA_READY_MARKER: ready with exceptions; owner meets",
        "recommendations": ["QA_REWRITE_MARKER: align documentation or verify behavior"],
        "evidence_ids": ["source-pricing"],
    }]
    store(bundle, root)
    before = (root / "bundle.json").read_bytes()
    for audience in ("owner", "buyer", "marketing"):
        html = render_report(bundle, audience)
        assert "QA_READY_MARKER" not in html
        assert "QA_REWRITE_MARKER" not in html
        assert "JSON" in html, "Excluding raw legacy prose needs a visible retention notice"
    assert (root / "bundle.json").read_bytes() == before
    assert "QA_READY_MARKER" in before.decode()


@pytest.mark.parametrize("field,value", [
    ("summary", "QA_OVERRIDE_MARKER: owner meets"),
    ("recommendations", ["QA_OVERRIDE_MARKER: rewrite facts before verification"]),
    ("fit", "meets"),
    ("text", "QA_OVERRIDE_MARKER: all requirements are met"),
    ("catalog", [{"id": "forged", "text": "QA_OVERRIDE_MARKER"}]),
])
def test_structured_extra_fields_fail_closed_even_when_render_called_directly(recorded_case, field, value):
    bundle, root = recorded_case
    proposal = proposal_for(bundle)
    proposal[field] = value
    bundle["agent_proposals"] = [proposal]
    with pytest.raises(ValueError):
        resolve_selection(bundle, proposal)
    for audience in ("owner", "buyer", "marketing"):
        html = render_report(bundle, audience)
        assert "QA_OVERRIDE_MARKER" not in html
    store(bundle, root)
    assert validate_bundle(root), "Validator must reject smuggled structured fields"


@pytest.mark.parametrize("mutation", ["unknown", "duplicate", "missing-required", "missing-evidence"])
def test_forged_or_incomplete_selections_do_not_publish_commentary(recorded_case, mutation):
    bundle, root = recorded_case
    proposal = proposal_for(bundle)
    if mutation == "unknown":
        proposal["review_item_ids"].append("QA_UNKNOWN_ITEM")
    elif mutation == "duplicate":
        proposal["review_item_ids"].append(proposal["review_item_ids"][0])
    elif mutation == "missing-required":
        proposal["review_item_ids"] = []
        proposal["evidence_ids"] = []
    else:
        proposal["evidence_ids"] = []
    bundle["agent_proposals"] = [proposal]
    with pytest.raises(ValueError):
        resolve_selection(bundle, proposal)
    html = render_report(bundle, "owner")
    assert "QA_UNKNOWN_ITEM" not in html
    store(bundle, root)
    assert validate_bundle(root)


@pytest.mark.parametrize("change", ["decision", "source", "task", "scope"])
def test_stale_selection_cannot_outlive_its_recorded_context(recorded_case, change):
    original, root = recorded_case
    proposal = proposal_for(original)
    bundle = deepcopy(original)
    if change == "decision":
        next(d for d in bundle["decisions"] if d["id"] == "decision-owner-alignment")["fit"] = "meets"
    elif change == "source":
        bundle["sources"][0]["values"]["price"] = 9
    elif change == "task":
        bundle["tasks"][0]["summary"] = "Different recorded task result"
    else:
        bundle["scope"]["plan"] = "Different scope"
    bundle["agent_proposals"] = [proposal]
    assert catalog_digest(bundle, proposal["role"]) != proposal["catalog_sha256"]
    with pytest.raises(ValueError):
        resolve_selection(bundle, proposal)
    render_report(bundle, "owner")  # Direct rendering must also fail closed, without crashing.
    store(bundle, root)
    assert validate_bundle(root)


def test_planning_selection_survives_only_normal_later_task_completion(recorded_case):
    complete, root = recorded_case
    before_tasks = deepcopy(complete)
    before_tasks["tasks"] = []
    before_tasks["decisions"] = []
    before_tasks["findings"] = []
    source_artifacts = {s["artifact_id"] for s in before_tasks["sources"] if s.get("artifact_id")}
    before_tasks["artifacts"] = [a for a in before_tasks["artifacts"] if a["id"] in source_artifacts]
    proposal = proposal_for(before_tasks, "requirements_researcher")
    assert catalog_digest(complete, proposal["role"]) == proposal["catalog_sha256"]
    assert resolve_selection(complete, proposal), "Normal task completion must not invalidate the earlier evidence plan"
    changed_source = deepcopy(complete)
    changed_source["sources"][0]["values"]["price"] = 9
    with pytest.raises(ValueError):
        resolve_selection(changed_source, proposal)
