"""Freshness metadata must be structurally linked, not merely labeled current."""
from __future__ import annotations
import json
from decision_recheck.engine import run_case
from decision_recheck.validate import validate_bundle
from helpers import brief_for


def stored_bundle(tmp_path):
    output = tmp_path / "run"
    return run_case(brief_for(), output), output


def save(output, bundle):
    path = output / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return path


def test_captured_source_observation_must_exist_in_freshness_objects(tmp_path):
    bundle, output = stored_bundle(tmp_path)
    bundle["sources"][0]["observation_id"] = "00000000-0000-4000-8000-000000000001"
    assert validate_bundle(save(output, bundle))


def test_reasoning_dependencies_cannot_reference_missing_observation(tmp_path):
    bundle, output = stored_bundle(tmp_path)
    first = next(iter(bundle["freshness"]["objects"]["reasoning"].values()))
    first["dependencies"] = ["00000000-0000-4000-8000-000000000002"]
    assert validate_bundle(save(output, bundle))


def test_freshness_objects_must_be_an_object(tmp_path):
    bundle, output = stored_bundle(tmp_path)
    bundle["freshness"]["objects"] = None
    assert validate_bundle(save(output, bundle))


def test_observation_map_must_be_an_object(tmp_path):
    bundle, output = stored_bundle(tmp_path)
    bundle["freshness"]["objects"]["observations"] = []
    assert validate_bundle(save(output, bundle))


def test_observation_ids_must_be_valid_scalar_identifiers(tmp_path):
    bundle, output = stored_bundle(tmp_path)
    first = next(iter(bundle["freshness"]["objects"]["observations"].values()))
    first["id"] = []
    assert validate_bundle(save(output, bundle))


def test_unavailable_required_source_prevents_whole_report_current_status(tmp_path):
    brief = brief_for()
    brief["sources"].append({"id": "missing-help", "kind": "help", "format": "json", "inline": {}, "fields": {"answer": "missing_answer"}})
    brief["requirements"].append({"id": "help-answer", "label": "Find an export answer", "source_id": "missing-help", "field": "answer", "operator": "contains", "expected": "Settings", "hard": True})
    bundle = run_case(brief, tmp_path / "run")
    assert bundle["status"] == "partial"
    assert bundle["freshness"]["state"] != "CURRENT"
    assert any(source["status"] == "unverifiable" for source in bundle["sources"])
