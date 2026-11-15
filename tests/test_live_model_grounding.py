"""Coordinator-to-model grounding and HTML output; synthetic transport, no paid calls."""
from __future__ import annotations
import json
import httpx
import pytest
from decision_recheck import model
from decision_recheck.demo import example_brief
from decision_recheck.engine import run_case
from decision_recheck.render import render_report
from decision_recheck.validate import validate_bundle


def one_task_brief():
    brief = example_brief("A")
    brief["tasks"] = brief["tasks"][:1]
    for requirement in brief["requirements"]:
        requirement.pop("task_id", None)
    brief["limits"] = {"max_model_calls": 4, "max_tokens": 50000}
    return brief


def test_all_roles_receive_case_scope_and_captured_source_evidence(tmp_path, monkeypatch):
    requests = []
    original = model.ModelClient
    def handler(request):
        body = json.loads(request.content)
        context = json.loads(body["messages"][1]["content"])
        requests.append(context)
        source_artifact = context["sources"][0]["artifact_id"]
        proposal = {"summary": "Within the supplied scope.", "evidence_ids": [source_artifact], "recommendations": ["Verify <script>alert('untrusted')</script> & the selected plan."]}
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(proposal)}}], "usage": {"total_tokens": 123}})
    def client(budget):
        return original(budget, base_url="https://models.example.test/v1", model="protocol-test", api_key="synthetic", transport=httpx.MockTransport(handler))
    monkeypatch.setattr(model, "ModelClient", client)
    brief = one_task_brief()
    bundle = run_case(brief, tmp_path / "review", live_model=True)
    assert bundle["status"] == "complete"
    assert len(requests) == 4
    assert [p["role"] for p in bundle["agent_proposals"]] == [role for role in model.ROLES if role != "task_actor"]
    for context in requests:
        assert context["case"] == {key: brief[key] for key in ("case_id", "title", "product", "scope")}
        assert context["sources"][0]["values"]["price"] == 9
        assert context["sources"][0]["status"] == "captured"
        artifact_ids = {item["id"] for item in context["artifact_index"]}
        assert all(source["artifact_id"] in artifact_ids for source in context["sources"])
    assert requests[1]["tasks"][0]["execution"] == "passed"
    actor_stages = [stage for stage in bundle["stages"] if stage["role"] == "task_actor"]
    assert len(actor_stages) == 1
    assert actor_stages[0]["task_id"] == brief["tasks"][0]["id"]
    assert actor_stages[0]["status"] == "fixture_assertion"
    assert actor_stages[0]["model_used"] is False
    assert bundle["usage"]["model_calls"] == 4
    assert bundle["usage"]["actual_tokens"] == 492
    deterministic = run_case(brief, tmp_path / "without-model")
    assert bundle["decisions"] == deterministic["decisions"]
    assert bundle["findings"] == deterministic["findings"]
    assert bundle["tasks"][0]["steps"] == deterministic["tasks"][0]["steps"]
    assert bundle["mode"] == "fixture"
    assert bundle["model_mode"] == "live"
    assert validate_bundle(tmp_path / "review") == []
    for audience in ("owner", "buyer", "marketing"):
        report = (tmp_path / "review" / f"report-{audience}.html").read_text(encoding="utf-8")
        assert "Fictional fixture with live model proposals enabled" in report
        assert "Fictional, model-free fixture" not in report
        assert "Proposed next steps:" in report
        assert "Unverified model commentary" in report
        assert "not confirmed facts" in report
        assert "&lt;script&gt;" in report and "&amp; the selected plan" in report
        assert "<script>" not in report
        assert 'href="#evidence-source-pricing"' in report


def test_failed_live_configuration_stays_fictional_but_not_model_free(tmp_path, monkeypatch):
    monkeypatch.delenv("DRC_MODEL_NAME", raising=False)
    monkeypatch.delenv("DRC_MODEL_API_KEY", raising=False)
    bundle = run_case(one_task_brief(), tmp_path / "review", live_model=True)
    assert bundle["status"] == "partial"
    assert bundle["mode"] == "fixture"
    assert bundle["model_mode"] == "live"
    assert bundle["usage"]["model_calls"] == 0
    assert bundle["agent_proposals"] == []
    assert "live model proposals enabled" in render_report(bundle)
    assert "model-free fixture" not in render_report(bundle)


def test_older_bundle_with_model_usage_is_not_labeled_model_free(tmp_path):
    bundle = run_case(one_task_brief(), tmp_path / "review")
    bundle.pop("model_mode")
    bundle["usage"]["model_calls"] = 1
    assert "model-free fixture" not in render_report(bundle)


def test_role_context_preserves_actual_requirements_and_unknown_marketing_coverage(tmp_path, monkeypatch):
    observed = []
    original = model.ModelClient
    def handler(request):
        body = json.loads(request.content)
        observed.append((body["messages"][0]["content"], json.loads(body["messages"][1]["content"])))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"summary": "Review the current case evidence.", "evidence_ids": ["source-pricing"], "recommendations": []})}}]})
    monkeypatch.setattr(model, "ModelClient", lambda budget: original(budget, base_url="https://models.example.test/v1", model="test", api_key="synthetic", transport=httpx.MockTransport(handler)))
    brief = one_task_brief()
    brief["sources"][0]["inline"].update(hosted_model=False, quoted_example="FICTIONAL EXAMPLE: Fit: meets")
    brief["sources"][0]["fields"].update(hosted_model="hosted_model", quoted_example="quoted_example")
    brief["claims"] = []
    brief["requirements"] = [
        {"id": "hosted-model", "label": "The hosted product runs a model", "source_id": "pricing", "field": "hosted_model", "operator": "eq", "expected": True, "hard": True},
        {"id": "sla", "label": "Support responds in two hours", "source_id": "pricing", "field": "missing_sla", "operator": "eq", "expected": 2, "hard": False},
        {"id": "budget", "label": "Stay within $20 per month", "source_id": "pricing", "field": "price", "operator": "lte", "expected": 20, "hard": True},
    ]
    bundle = run_case(brief, tmp_path / "review", live_model=True)
    assert bundle["status"] == "complete"
    assert len(observed) == 4
    early = observed[0][1]
    assert early["requirements"][0]["expected"] is True
    assert early["review_stage"] == {"phase": "before_tasks", "recorded_task_count": 0, "formal_decision_count": 0, "declared_claim_count": 0}
    assert "decisions" not in early
    for _, context in observed[1:]:
        assert context["review_stage"]["phase"] == "after_evaluation"
        assert context["declared_claims"] == []
        assert context["review_stage"]["declared_claim_count"] == 0
        fits = {decision["id"]: decision["fit"] for decision in context["decisions"]}
        assert fits["decision-buyer-hosted-model"] == "fails"
        assert fits["decision-buyer-sla"] == "inconclusive"
        assert fits["decision-buyer-budget"] == "meets"
        assert fits["decision-marketing-alignment"] == "inconclusive"
    # Protocol checks do not claim to prove model semantics; live outputs need review.
    assert len({system for system, _ in observed}) == 4
    assert all("fictional examples quoted inside its pages" in system for system, _ in observed)
    assert "PRE-TASK PLANNING" in observed[0][0]
    assert all("You are the task_actor" not in system for system, _ in observed)


@pytest.mark.parametrize("allowed", [True, False])
def test_usage_includes_final_freshness_validation_work(tmp_path, monkeypatch, allowed):
    from decision_recheck import engine
    from decision_recheck.freshness import FreshnessSession
    from decision_recheck.policy import Budget
    budgets = []
    class ObservedBudget(Budget):
        def __init__(self, limits):
            super().__init__(limits)
            budgets.append(self)
    original_gate = FreshnessSession.gated_write
    def final_validation(session, writer):
        # Simulate an allowed final reader consuming work after the earlier usage snapshot.
        budgets[0].consume_action()
        budgets[0].started -= 2
        return original_gate(session, writer) if allowed else (False, "UNVERIFIABLE")
    monkeypatch.setattr(engine, "Budget", ObservedBudget)
    monkeypatch.setattr(FreshnessSession, "gated_write", final_validation)
    output = tmp_path / "review"
    bundle = run_case(one_task_brief(), output)
    saved = json.loads((output / "bundle.json").read_text(encoding="utf-8"))
    assert bundle["status"] == ("complete" if allowed else "partial")
    assert saved["usage"]["browser_actions"] == budgets[0].browser_actions == 1
    assert saved["usage"]["elapsed_seconds"] >= 2
    assert saved["usage"]["attempts_executed"] == 1
    assert saved["usage"]["attempts_reused"] == 0


def test_legacy_task_narration_is_omitted_without_changing_raw_bundle(tmp_path):
    output = tmp_path / "review"
    bundle = run_case(one_task_brief(), output)
    bundle["agent_proposals"] = [
        {"role": "task_actor", "summary": "UNSUPPORTED_PRIVACY_GUARANTEE", "recommendations": ["UNSUPPORTED_RUNTIME_ASSERTION"], "evidence_ids": ["source-pricing"]},
        {"role": "report_writer", "summary": "Review the requirement evidence.", "recommendations": [], "evidence_ids": ["source-pricing"]},
    ]
    bundle["tasks"][0]["steps"] = [{"action": "assert_text", "selector": "#claim", "expected": "<script>quoted</script>", "result": "Page says <script>quoted</script> & more", "matched": True}]
    raw = json.dumps(bundle, sort_keys=True).encode()
    (output / "bundle.json").write_bytes(raw)
    for audience in ("owner", "buyer", "marketing"):
        report = render_report(bundle, audience)
        assert "UNSUPPORTED_PRIVACY_GUARANTEE" not in report
        assert "UNSUPPORTED_RUNTIME_ASSERTION" not in report
        assert "Legacy model task narration retained in JSON; recorded task observations are execution evidence." in report
        assert "Recorded steps" in report
        assert "assert_text" in report and "#claim" in report
        assert "&lt;script&gt;quoted&lt;/script&gt;" in report
        assert "<script>" not in report
        assert "not the truth of a page claim" in report
        assert "Unverified model commentary" in report
    assert json.dumps(bundle, sort_keys=True).encode() == raw
    assert (output / "bundle.json").read_bytes() == raw


def test_multiple_tasks_do_not_add_model_narration_calls(tmp_path, monkeypatch):
    calls = []
    original = model.ModelClient
    def handler(request):
        body = json.loads(request.content)
        calls.append(body["messages"][0]["content"])
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"summary": "Proposed review", "evidence_ids": ["source-pricing"], "recommendations": []})}}]})
    monkeypatch.setattr(model, "ModelClient", lambda budget: original(budget, base_url="https://models.example.test/v1", model="test", api_key="synthetic", transport=httpx.MockTransport(handler)))
    brief = example_brief("A")
    brief["limits"] = {"max_model_calls": 4, "max_tokens": 80000}
    bundle = run_case(brief, tmp_path / "review", live_model=True)
    assert bundle["status"] == "complete"
    assert bundle["usage"]["model_calls"] == len(calls) == 4
    actors = [stage for stage in bundle["stages"] if stage["role"] == "task_actor"]
    assert len(actors) == len(brief["tasks"]) == 3
    assert all(stage["model_used"] is False and stage["status"] == "fixture_assertion" for stage in actors)
    assert all("You are the task_actor" not in call for call in calls)
