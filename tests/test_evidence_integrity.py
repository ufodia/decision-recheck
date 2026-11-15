"""Evidence integrity and safe report boundaries, using real generated bundles."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import pytest
from decision_recheck.engine import run_case
from decision_recheck.render import render_report
from decision_recheck.validate import validate_bundle
from helpers import brief_for


def write_changed_bundle(output: Path, bundle: dict) -> Path:
    path = output / "bundle.json"
    path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize("bad_path", ["../outside.json", "../../outside.json", "..\\outside.json", "/outside.json", "C:\\outside.json"])
def test_artifact_paths_cannot_escape_bundle(tmp_path, bad_path):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    assert bundle["artifacts"], "The observed source must be captured"
    bundle["artifacts"][0]["path"] = bad_path
    assert validate_bundle(write_changed_bundle(output, bundle)), "Unsafe artifact locator must be rejected"


def test_artifact_replacement_is_detected(tmp_path):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    artifact = bundle["artifacts"][0]
    artifact_path = (output / artifact["path"]).resolve()
    assert artifact_path.is_relative_to(output.resolve())
    artifact_path.write_text("This is different evidence, despite the same filename.", encoding="utf-8")
    assert validate_bundle(output / "bundle.json"), "Changed bytes cannot retain verified integrity"


def test_nonexistent_artifact_is_detected(tmp_path):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    bundle["artifacts"][0]["path"] = "artifacts/missing-evidence.json"
    assert validate_bundle(write_changed_bundle(output, bundle))


def test_fabricated_decision_evidence_reference_is_rejected(tmp_path):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    assert bundle["decisions"]
    bundle["decisions"][0]["evidence_ids"] = ["source-that-was-never-captured"]
    assert validate_bundle(write_changed_bundle(output, bundle))


def test_duplicate_artifact_ids_are_rejected(tmp_path):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    bundle["artifacts"].append(deepcopy(bundle["artifacts"][0]))
    assert validate_bundle(write_changed_bundle(output, bundle))


def test_missing_schema_version_does_not_validate_as_a_current_bundle(tmp_path):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    bundle.pop("schema_version", None)
    assert validate_bundle(write_changed_bundle(output, bundle))


@pytest.mark.parametrize("view", ["owner", "buyer", "marketing"])
def test_report_escapes_untrusted_product_and_requirement_text(tmp_path, view):
    payload = '<img src=x onerror="alert(1)">'
    brief = brief_for()
    brief["product"] = payload
    brief["title"] = payload
    brief["requirements"][0]["label"] = payload
    bundle = run_case(brief, tmp_path / "run")
    html = render_report(bundle, view)
    assert payload not in html
    assert "&lt;img" in html
    assert "http-equiv" in html.lower() and "content-security-policy" in html.lower()


def test_malformed_json_bundle_is_a_validation_result_not_a_crash(tmp_path):
    path = tmp_path / "bundle.json"
    path.write_text('{"artifacts":', encoding="utf-8")
    errors = validate_bundle(path)
    assert isinstance(errors, list) and errors

@pytest.mark.parametrize("category,record", [("artifacts", {"id": [], "path": "missing"}), ("artifacts", {"id": {}, "path": "missing"}), ("findings", None), ("decisions", []), ("decisions", None), ("sources", {"id": "source-malformed", "artifact_id": "source-offer", "evidence_ids": None}), ("sources", {"id": "source-malformed", "artifact_id": "source-offer", "evidence_ids": {}}), ("findings", {"id": "finding-bad", "severity": "high", "evidence_ids": None})])
def test_malformed_record_shape_returns_errors_without_validation_crash(tmp_path, category, record):
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    bundle[category] = [record]
    errors = validate_bundle(write_changed_bundle(output, bundle))
    assert isinstance(errors, list) and errors

@pytest.mark.parametrize("literal_path", ["artifacts/%2e%2e/%2e%2e/outside.txt", "artifacts/quarter#1.txt", "artifacts/export file.txt"])
def test_report_artifact_links_refer_to_exact_validated_literal_file(tmp_path, literal_path):
    from html import unescape
    import re
    from urllib.parse import unquote, urlsplit
    output = tmp_path / "run"
    bundle = run_case(brief_for(), output)
    record = bundle["artifacts"][0]
    original = output / record["path"]
    destination = output / literal_path
    assert destination.resolve().is_relative_to(output.resolve())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(original.read_bytes())
    record["path"] = literal_path
    assert validate_bundle(write_changed_bundle(output, bundle)) == []
    html = render_report(bundle, "owner")
    match = re.search(r'href="([^"]+)">Open artifact</a>', html)
    assert match
    parsed = urlsplit(unescape(match.group(1)))
    assert parsed.query == "" and parsed.fragment == ""
    assert unquote(parsed.path) == literal_path


def test_artifact_query_characters_are_encoded_as_literal_path_text():
    from urllib.parse import unquote, urlsplit
    from decision_recheck.render import artifact_link
    literal_path = "artifacts/offer?plan=Starter.txt"
    parsed = urlsplit(artifact_link({"path": literal_path}))
    assert parsed.query == "" and parsed.fragment == ""
    assert unquote(parsed.path) == literal_path
