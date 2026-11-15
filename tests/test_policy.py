"""Allowlist controls must run before a network request or browser action."""
from __future__ import annotations
import pytest
from decision_recheck.policy import PolicyError, check_url


PUBLIC = {"allowed_hosts": ["example.com"], "allow_private_network": False, "allow_test_writes": False, "allowed_actions": ["read", "assert_text"]}


@pytest.mark.parametrize("url", [
    "https://example.com.evil.test/pricing",
    "https://example.com@evil.test/pricing",
    "file:///C:/Windows/win.ini",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "ftp://example.com/pricing",
    "http://127.0.0.1/pricing",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/pricing",
    "http://localhost/pricing",
])
def test_unapproved_network_targets_are_rejected(url):
    with pytest.raises(PolicyError): check_url(url, PUBLIC)


def test_loopback_requires_explicit_test_network_permission():
    permissions = {**PUBLIC, "allowed_hosts": ["127.0.0.1"]}
    with pytest.raises(PolicyError): check_url("http://127.0.0.1:8080/source", permissions)


def test_local_fixture_can_be_explicitly_authorized():
    permissions = {**PUBLIC, "allowed_hosts": ["127.0.0.1"], "allow_private_network": True}
    check_url("http://127.0.0.1:8080/source", permissions)
