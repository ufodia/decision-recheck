"""Strict operator configuration and finite resource limits."""
from __future__ import annotations
from copy import deepcopy
import math
import pytest
from decision_recheck.models import BriefError, load_brief
from decision_recheck.policy import Budget, BudgetExceeded, PolicyError, check_action
from helpers import brief_for


@pytest.mark.parametrize("name", ["allow_private_network", "allow_test_writes"])
@pytest.mark.parametrize("value", ["false", "true", 1, [], {}])
def test_permission_flags_are_actual_booleans(name, value):
    brief = brief_for()
    brief["permissions"][name] = value
    with pytest.raises(BriefError): load_brief(brief)


@pytest.mark.parametrize("field", ["max_browser_actions", "max_model_calls", "max_tokens", "max_response_bytes"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), 0.5, True, -1])
def test_count_caps_are_finite_nonnegative_integers(field, value):
    brief = brief_for()
    brief["limits"][field] = value
    with pytest.raises(BriefError): load_brief(brief)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True])
def test_deadline_is_finite_nonnegative_seconds(value):
    brief = brief_for()
    brief["limits"]["timeout_seconds"] = value
    with pytest.raises(BriefError): load_brief(brief)


@pytest.mark.parametrize("field,value", [("scope", []), ("limits", []), ("permissions", []), ("scope", "Starter")])
def test_container_shape_errors_are_explicit_brief_errors(field, value):
    brief = brief_for()
    brief[field] = value
    with pytest.raises(BriefError): load_brief(brief)


@pytest.mark.parametrize("action", ["purchase", "send_message", "cancel_subscription", "execute_python", "shell"])
def test_production_side_effect_actions_are_not_available(action):
    with pytest.raises(PolicyError): check_action(action, {"allowed_actions": ["read", "assert_text"], "allow_test_writes": False})


@pytest.mark.parametrize("action", ["click", "fill", "download"])
def test_declared_interactive_action_still_requires_test_write_permission(action):
    with pytest.raises(PolicyError): check_action(action, {"allowed_actions": [action], "allow_test_writes": False})


def test_model_call_cap_stops_before_an_extra_call():
    budget = Budget({"max_model_calls": 1, "max_tokens": 1000})
    budget.consume_model(500)
    with pytest.raises(BudgetExceeded): budget.consume_model(1)
    assert budget.model_calls == 1


def test_token_reservation_cap_stops_before_dispatch():
    budget = Budget({"max_model_calls": 10, "max_tokens": 500})
    budget.consume_model(400)
    with pytest.raises(BudgetExceeded): budget.consume_model(101)
    assert budget.model_calls == 1
    assert budget.reserved_tokens == 400


def test_browser_action_cap_stops_before_an_extra_action():
    budget = Budget({"max_browser_actions": 1})
    budget.consume_action()
    with pytest.raises(BudgetExceeded): budget.consume_action()
    assert budget.browser_actions == 1


def test_zero_deadline_stops_immediately():
    with pytest.raises(BudgetExceeded): Budget({"timeout_seconds": 0}).check_time()
