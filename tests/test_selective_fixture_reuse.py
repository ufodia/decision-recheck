"""Selective fixture reuse is explicit historical evidence; browser tasks stay fresh."""
from __future__ import annotations
from copy import deepcopy
from decision_recheck import engine
from decision_recheck.demo import example_brief
from test_browser_boundaries import installed_browser
from test_task_decisions import task_brief


def spy_task_runs(monkeypatch):
    calls = []
    original = engine.run_task
    def tracked(task, *args, **kwargs):
        calls.append(task["id"])
        return original(task, *args, **kwargs)
    monkeypatch.setattr(engine, "run_task", tracked)
    return calls


def test_pure_fixture_footer_control_reuses_historical_attempts_explicitly(tmp_path, monkeypatch):
    brief = example_brief("A")
    baseline_dir = tmp_path / "before"
    before = engine.run_case(brief, baseline_dir)
    calls = spy_task_runs(monkeypatch)
    after = engine.run_case(example_brief("footer"), tmp_path / "after", baseline=baseline_dir)
    assert calls == []
    assert after["usage"]["attempts_executed"] == 0
    assert after["usage"]["attempts_reused"] == 3
    old_tasks = {task["id"]: task for task in before["tasks"]}
    for task in after["tasks"]:
        assert task["method"] == "reused_historical"
        assert task["reused_from"] == before["run_id"]
        assert task["checked_at"] == old_tasks[task["id"]]["checked_at"]
        assert task["steps"] == old_tasks[task["id"]]["steps"]
    assert any("not freshly executed" in warning for warning in after["warnings"])


def test_changed_task_spec_runs_again_even_with_unchanged_source(tmp_path, monkeypatch):
    brief = example_brief("A")
    baseline_dir = tmp_path / "before"
    engine.run_case(brief, baseline_dir)
    calls = spy_task_runs(monkeypatch)
    changed = deepcopy(brief)
    changed["tasks"][0]["title"] = "A deliberately changed review task"
    after = engine.run_case(changed, tmp_path / "after", baseline=baseline_dir)
    assert calls == [changed["tasks"][0]["id"]]
    assert after["usage"]["attempts_executed"] == 1
    assert after["usage"]["attempts_reused"] == 2


def test_scope_change_prevents_historical_fixture_reuse(tmp_path, monkeypatch):
    brief = example_brief("A")
    baseline_dir = tmp_path / "before"
    engine.run_case(brief, baseline_dir)
    calls = spy_task_runs(monkeypatch)
    changed = deepcopy(brief)
    changed["scope"]["locale"] = "en-GB"
    after = engine.run_case(changed, tmp_path / "after", baseline=baseline_dir)
    assert len(calls) == 3
    assert after["usage"]["attempts_reused"] == 0


def test_real_browser_attempt_is_not_reused_from_unchanged_document_fields(tmp_path, monkeypatch, local_sources, installed_browser):
    local_sources.html("/export", '<div id="result">CSV exported successfully</div>')
    brief = task_brief(local_sources)
    brief["tasks"][0].update({"depends_on": ["offer"], "dependencies_complete": True})
    baseline_dir = tmp_path / "before"
    before = engine.run_case(brief, baseline_dir)
    assert before["tasks"][0]["execution"] == "passed"
    calls = spy_task_runs(monkeypatch)
    after = engine.run_case(brief, tmp_path / "after", baseline=baseline_dir)
    assert calls == ["export-task"]
    assert after["tasks"][0]["method"] == "browser"
    assert after["usage"]["attempts_reused"] == 0
