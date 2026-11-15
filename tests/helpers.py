"""Independent business-case inputs shared by tests."""

def brief_for(operator="lte", expected=20, actual=9):
    return {
        "case_id": "qa-offer",
        "product": "Synthetic SaaS",
        "title": "Independent offer acceptance scenario",
        "scope": {"plan": "Starter", "locale": "en-US", "currency": "USD", "billing_period": "month"},
        "sources": [{
            "id": "offer", "kind": "pricing", "format": "json",
            "inline": {"value": actual, "plan": "Starter", "currency": "USD", "footer": "Copyright 2026"},
            "fields": {"value": "value", "plan": "plan", "currency": "currency"},
        }],
        "requirements": [
            {"id": "criterion", "label": "Declared buyer requirement", "source_id": "offer", "field": "value", "operator": operator, "expected": expected, "hard": True},
            {"id": "plan", "label": "Selected plan", "source_id": "offer", "field": "plan", "operator": "eq", "expected": "Starter", "hard": True},
            {"id": "currency", "label": "Comparison currency", "source_id": "offer", "field": "currency", "operator": "eq", "expected": "USD", "hard": True},
        ],
        "claims": [], "tasks": [],
        "permissions": {"allowed_hosts": [], "allow_private_network": False, "allow_test_writes": False, "allowed_actions": ["read", "assert_text"]},
        "limits": {"max_browser_actions": 36, "max_model_calls": 40, "max_tokens": 12000, "timeout_seconds": 1200, "max_response_bytes": 1000000},
    }
