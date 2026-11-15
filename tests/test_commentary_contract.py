"""The live adapter cannot turn model prose into contradictory report content."""
from __future__ import annotations

from copy import deepcopy
import json

import httpx
import pytest

from decision_recheck.commentary import CONTRACT, CanonicalSelectionError, catalog_for_role, catalog_digest, resolve_selection
from decision_recheck.demo import example_brief
from decision_recheck.engine import run_case
from decision_recheck.model import ModelClient, safe_model_failure
from decision_recheck.policy import Budget


@pytest.fixture
def recorded_case(tmp_path):
    brief = example_brief("B")
    return run_case(brief, tmp_path / "recorded")


def request_context(bundle):
    role = "report_writer"
    return {"review_catalog": catalog_for_role(bundle, role),
            "review_catalog_digest": catalog_digest(bundle, role)}


def required_ids(context):
    return [item["id"] for item in context["review_catalog"] if item["required"]]


def make_client(answer, requests):
    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "chatcmpl-synthetic-selection", "model": "snapshot-test", "created": 100,
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(answer)}}],
            "usage": {"total_tokens": 123},
        })
    return ModelClient(Budget({"max_tokens": 80000}), base_url="https://models.example.test/v1",
                       model="configured-test", api_key="synthetic", transport=httpx.MockTransport(handler))


def test_adapter_accepts_only_selections_and_derives_citations(recorded_case):
    context = request_context(recorded_case)
    selection = list(reversed(required_ids(context)))
    requests = []
    client = make_client({"review_item_ids": selection}, requests)
    result = client.propose("report_writer", context, {a["id"] for a in recorded_case["artifacts"]})
    assert result["commentary_contract"] == CONTRACT
    assert result["review_item_ids"] == selection
    assert "summary" not in result and "recommendations" not in result
    entries = resolve_selection(recorded_case, result)
    assert [entry["id"] for entry in entries] == selection
    owner = next(entry for entry in entries if entry.get("decision_id") == "decision-owner-alignment")
    assert owner["fit"] == "fails"
    assert owner["text"].endswith(": fails.")
    assert any("before changing a documented fact" in entry["text"] for entry in entries)
    assert client.budget.actual_tokens == result["provider_total_tokens"] == 123
    assert len(requests) == client.budget.model_calls == 1
    assert "ONLY review_item_ids" in requests[0]["messages"][0]["content"]
    dispatched = json.loads(requests[0]["messages"][1]["content"])
    assert dispatched["required_review_item_ids"] == required_ids(context)
    assert dispatched["selection_response_example"] == {"review_item_ids": required_ids(context)}
    assert "Copy the ENTIRE required_review_item_ids list" in requests[0]["messages"][0]["content"]


@pytest.mark.parametrize("problem", [
    "unknown", "duplicate", "missing_required", "scalar", "empty", "summary",
    "recommendations", "fit_override", "citation_override",
])
def test_invalid_provider_selection_is_rejected_without_retry(recorded_case, problem):
    context = request_context(recorded_case)
    ids = required_ids(context)
    answer = {"review_item_ids": ids}
    if problem == "unknown": answer["review_item_ids"] = ids + ["invented"]
    if problem == "duplicate": answer["review_item_ids"] = ids + ids[:1]
    if problem == "missing_required": answer["review_item_ids"] = ids[1:]
    if problem == "scalar": answer["review_item_ids"] = "evidence-rule"
    if problem == "empty": answer["review_item_ids"] = []
    if problem == "summary": answer["summary"] = "The product is ready with exceptions."
    if problem == "recommendations": answer["recommendations"] = ["Change documentation before verifying behavior."]
    if problem == "fit_override": answer["fit"] = "meets"
    if problem == "citation_override": answer["evidence_ids"] = ["invented"]
    requests = []
    client = make_client(answer, requests)
    with pytest.raises(ValueError):
        client.propose("report_writer", context, {a["id"] for a in recorded_case["artifacts"]})
    assert client.budget.actual_tokens == 123
    assert len(requests) == client.budget.model_calls == 1


def test_missing_required_items_has_safe_fixed_diagnostic(recorded_case):
    context = request_context(recorded_case)
    requests = []
    client = make_client({"review_item_ids": required_ids(context)[1:]}, requests)
    with pytest.raises(CanonicalSelectionError) as raised:
        client.propose("report_writer", context, {a["id"] for a in recorded_case["artifacts"]})
    failure = safe_model_failure(raised.value)
    assert failure["category"] == "selection_contract_rejected"
    assert failure["selection_code"] == "missing_required_items"
    assert client.budget.actual_tokens == 123
    assert len(requests) == 1


def test_invalid_response_fields_cannot_enter_diagnostic_text(recorded_case):
    context = request_context(recorded_case)
    requests = []
    client = make_client({"review_item_ids": required_ids(context), "summary": "private-provider-body"}, requests)
    with pytest.raises(CanonicalSelectionError) as raised:
        client.propose("report_writer", context, {a["id"] for a in recorded_case["artifacts"]})
    assert "private-provider-body" not in str(raised.value)
    assert safe_model_failure(raised.value)["selection_code"] == "invalid_response_shape"
    assert "private-provider-body" not in json.dumps(safe_model_failure(raised.value))
    assert client.budget.actual_tokens == 123


def test_selection_binding_cannot_be_moved_to_another_run(recorded_case):
    context = request_context(recorded_case)
    requests = []
    result = make_client({"review_item_ids": required_ids(context)}, requests).propose(
        "report_writer", context, {a["id"] for a in recorded_case["artifacts"]})
    other = deepcopy(recorded_case)
    other["run_id"] = "different-run"
    with pytest.raises(ValueError, match="current run"):
        resolve_selection(other, result)


def test_live_coordinator_rejects_contradictory_prose_and_preserves_formal_results(tmp_path, monkeypatch):
    from decision_recheck import model
    requests = []
    original = model.ModelClient
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "summary": "Ready with exceptions", "recommendations": ["Rewrite facts without checking behavior"],
            "evidence_ids": [],
        })}}], "usage": {"total_tokens": 123}})
    monkeypatch.setattr(model, "ModelClient", lambda budget: original(
        budget, base_url="https://models.example.test/v1", model="test", api_key="synthetic",
        transport=httpx.MockTransport(handler)))
    brief = example_brief("B")
    brief["limits"] = {"max_model_calls": 4, "max_tokens": 80000}
    baseline = run_case(brief, tmp_path / "without-model")
    reviewed = run_case(brief, tmp_path / "with-model", live_model=True)
    assert reviewed["status"] == "partial"
    assert reviewed["decisions"] == baseline["decisions"]
    assert reviewed["agent_proposals"] == []
    assert reviewed["usage"]["model_calls"] == len(requests) == 4
    assert reviewed["usage"]["actual_tokens"] == 492
    failures = [stage for stage in reviewed["stages"] if stage.get("status") == "blocked"]
    assert len(failures) == 4
    assert all(stage["failure"]["selection_code"] == "invalid_response_shape" for stage in failures)
    assert all("invalid_response_shape" in warning for warning in reviewed["warnings"] if "incomplete:" in warning)
    for role in ("owner", "buyer", "marketing"):
        html = (tmp_path / "with-model" / f"report-{role}.html").read_text(encoding="utf-8")
        assert "Ready with exceptions" not in html
        assert "Rewrite facts without checking behavior" not in html
