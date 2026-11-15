"""Independent SaaS offer scenarios: 20 planted mismatches and 20 clean controls."""
from __future__ import annotations
from copy import deepcopy
import pytest
from decision_recheck.engine import run_case
from decision_recheck.validate import validate_bundle


# These are declared business expectations, not outputs computed by the implementation.
MISMATCHES = [
    ("price-21", "lte", 20, 21),
    ("price-29", "lte", 20, 29),
    ("price-49", "lte", 20, 49),
    ("price-99", "lte", 20, 99),
    ("price-one-cent-over", "lte", 20, 20.01),
    ("csv-entitlement", "eq", True, False),
    ("api-entitlement", "eq", "included", "Pro only"),
    ("seat-entitlement", "eq", 5, 1),
    ("retention-entitlement", "eq", 90, 7),
    ("region-entitlement", "eq", "EU", "US"),
    ("help-export", "contains", "CSV export", "Download a PDF report"),
    ("help-cancel", "contains", "cancel subscription", "Please contact sales"),
    ("help-billing", "contains", "monthly billing", "Annual invoices only"),
    ("help-support", "contains", "email support", "Community forum only"),
    ("help-sso", "contains", "single sign-on", "Password login"),
    ("currency", "eq", "USD", "EUR"),
    ("billing-period", "eq", "month", "year"),
    ("plan-name", "eq", "Starter", "Pro"),
    ("export-format", "eq", "CSV", "PDF"),
    ("accessibility-route", "eq", "keyboard", "pointer only"),
]
CLEAN_CONTROLS = [
    ("price-free", "lte", 20, 0),
    ("price-nine", "lte", 20, 9),
    ("price-nineteen", "lte", 20, 19),
    ("price-exact-limit", "lte", 20, 20),
    ("price-cent-below", "lte", 20, 19.99),
    ("csv-included", "eq", True, True),
    ("api-included", "eq", "included", "included"),
    ("seats-five", "eq", 5, 5),
    ("retention-ninety", "eq", 90, 90),
    ("region-eu", "eq", "EU", "EU"),
    ("help-export-present", "contains", "CSV export", "Use CSV export from Settings"),
    ("help-cancel-present", "contains", "cancel subscription", "You can cancel subscription from Billing"),
    ("help-billing-present", "contains", "monthly billing", "Choose monthly billing or annual billing"),
    ("help-support-present", "contains", "email support", "Starter includes email support"),
    ("help-sso-present", "contains", "single sign-on", "Configure single sign-on in Security"),
    ("currency-usd", "eq", "USD", "USD"),
    ("billing-month", "eq", "month", "month"),
    ("plan-starter", "eq", "Starter", "Starter"),
    ("format-csv", "eq", "CSV", "CSV"),
    ("keyboard-route", "eq", "keyboard", "keyboard"),
]


from helpers import brief_for


def buyer_fit(bundle, requirement_id="criterion"):
    decisions = [d for d in bundle["decisions"] if d.get("audience") == "buyer" and d.get("requirement_id") == requirement_id]
    assert len(decisions) == 1, f"A requirement needs exactly one buyer result: {decisions}"
    return decisions[0]["fit"]


@pytest.mark.parametrize("label,operator,expected,actual", MISMATCHES, ids=[c[0] for c in MISMATCHES])
def test_planted_mismatch_fails_declared_requirement(tmp_path, label, operator, expected, actual):
    output = tmp_path / label
    bundle = run_case(brief_for(operator, expected, actual), output)
    assert buyer_fit(bundle) == "fails"
    assert buyer_fit(bundle, "plan") == "meets"
    assert buyer_fit(bundle, "currency") == "meets"
    assert validate_bundle(output / "bundle.json") == []


@pytest.mark.parametrize("label,operator,expected,actual", CLEAN_CONTROLS, ids=[c[0] for c in CLEAN_CONTROLS])
def test_clean_control_meets_declared_requirement(tmp_path, label, operator, expected, actual):
    output = tmp_path / label
    bundle = run_case(brief_for(operator, expected, actual), output)
    assert buyer_fit(bundle) == "meets"
    assert validate_bundle(output / "bundle.json") == []


def test_hard_budget_failure_is_not_averaged_away_by_passing_features(tmp_path):
    bundle = run_case(brief_for(actual=49), tmp_path / "run")
    assert buyer_fit(bundle) == "fails"
    assert buyer_fit(bundle, "plan") == "meets"
    assert buyer_fit(bundle, "currency") == "meets"


def test_missing_declared_field_is_unknown_not_feature_absent(tmp_path):
    brief = brief_for("eq", True, True)
    del brief["sources"][0]["inline"]["value"]
    bundle = run_case(brief, tmp_path / "run")
    assert buyer_fit(bundle) in {"inconclusive", "conditional"}
    assert buyer_fit(bundle) != "fails"


def test_footer_only_change_does_not_change_scoped_fit(tmp_path):
    brief = brief_for()
    baseline = tmp_path / "before"
    old = run_case(brief, baseline)
    modified = deepcopy(brief)
    modified["sources"][0]["inline"]["footer"] = "A new copyright notice and decorative link"
    new = run_case(modified, tmp_path / "after", baseline=baseline / "bundle.json")
    assert buyer_fit(old) == buyer_fit(new) == "meets"

@pytest.mark.parametrize("value", ["", "   ", None])
def test_empty_selected_field_is_inconclusive_not_a_contradiction(tmp_path, value):
    brief = brief_for("contains", "CSV", value)
    bundle = run_case(brief, tmp_path / "run")
    assert buyer_fit(bundle) in {"inconclusive", "conditional"}


def test_dependency_recheck_marks_only_changed_source_dependents(tmp_path):
    brief = brief_for()
    brief["sources"].append({"id": "help", "kind": "help", "format": "json", "inline": {"answer": "CSV export is in Settings"}, "fields": {"answer": "answer"}})
    brief["requirements"].append({"id": "help-route", "label": "Find export guidance", "source_id": "help", "field": "answer", "operator": "contains", "expected": "Settings", "hard": True})
    baseline = tmp_path / "before"
    run_case(brief, baseline)
    changed = deepcopy(brief)
    changed["sources"][0]["inline"]["value"] = 49
    bundle = run_case(changed, tmp_path / "after", baseline=baseline / "bundle.json")
    changes = {change["source_id"]: change for change in bundle["changes"]}
    assert changes["offer"]["state"] == "STALE_SOURCE"
    assert "decision-buyer-criterion" in changes["offer"]["affected_ids"]
    assert "decision-buyer-help-route" not in changes["offer"]["affected_ids"]
    assert changes["help"]["state"] == "CURRENT"
    assert changes["help"]["affected_ids"] == []


def test_irrelevant_footer_edit_preserves_freshctx_current_state(tmp_path):
    brief = brief_for()
    baseline = tmp_path / "before"
    run_case(brief, baseline)
    brief["sources"][0]["inline"]["footer"] = "Decorative copyright update"
    bundle = run_case(brief, tmp_path / "after", baseline=baseline / "bundle.json")
    assert bundle["changes"]
    assert all(change["state"] == "CURRENT" for change in bundle["changes"])
