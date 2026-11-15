"""Configured run deadlines also bound individual I/O calls."""
from __future__ import annotations
import httpx
import pytest
from decision_recheck import collector, model
from decision_recheck.policy import Budget


def fixed_near_deadline_budget(monkeypatch):
    monkeypatch.setattr("time.monotonic", lambda: 1000.0)
    budget = Budget({"timeout_seconds": 0.05})
    budget.started = 999.96
    return budget


def test_http_timeout_cannot_exceed_remaining_run_time(monkeypatch):
    budget = fixed_near_deadline_budget(monkeypatch)
    timeouts = []
    original_client = httpx.Client
    def client(*args, **kwargs):
        timeouts.append(kwargs["timeout"])
        kwargs["transport"] = httpx.MockTransport(lambda request: httpx.Response(200, content=b'{"price":9}'))
        return original_client(*args, **kwargs)
    monkeypatch.setattr(collector.httpx, "Client", client)
    permissions = {"allowed_hosts": ["127.0.0.1"], "allow_private_network": True}
    collector.fetch_http("http://127.0.0.1/pricing", permissions, budget)
    assert timeouts and 0 < timeouts[0] <= 0.011


def test_model_timeout_cannot_exceed_remaining_run_time(monkeypatch):
    budget = fixed_near_deadline_budget(monkeypatch)
    timeouts = []
    original_client = httpx.Client
    def client(*args, **kwargs):
        timeouts.append(kwargs["timeout"])
        return original_client(*args, **kwargs)
    monkeypatch.setattr(model.httpx, "Client", client)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"choices": [{"message": {"content": '{"summary":"A proposal","evidence_ids":[],"recommendations":[]}'}}]}))
    instance = model.ModelClient(budget, base_url="https://models.example.test/v1", model="protocol-test", api_key="synthetic", transport=transport)
    instance.propose("report_writer", {}, set())
    assert timeouts and 0 < timeouts[0] <= 0.011
