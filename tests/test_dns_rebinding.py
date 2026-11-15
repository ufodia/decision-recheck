"""Local-only DNS rebinding regression; no public address is contacted."""
from __future__ import annotations
import ipaddress
import socket
from decision_recheck.collector import fetch_http
from decision_recheck.policy import Budget


def test_dns_rebinding_cannot_turn_a_public_check_into_a_private_connection(monkeypatch, local_sources):
    local_sources.json("/source", {"private_fixture": "must never be read"})
    port = int(local_sources.base_url.rsplit(":", 1)[1])
    original_resolve = socket.getaddrinfo
    original_connect = socket.socket.connect
    calls = []
    def rebinding_resolve(host, target_port, *args, **kwargs):
        normalized = host.decode() if isinstance(host, bytes) else host
        if normalized == "rebind.example.test":
            calls.append(normalized)
            return original_resolve("93.184.216.34" if len(calls) == 1 else "127.0.0.1", target_port, *args, **kwargs)
        return original_resolve(host, target_port, *args, **kwargs)
    def only_local_fixture_connections(sock, address):
        try: allowed = ipaddress.ip_address(address[0]).is_loopback
        except ValueError: allowed = False
        if not allowed: raise OSError("External network intentionally blocked by this local-only test")
        return original_connect(sock, address)
    monkeypatch.setattr(socket, "getaddrinfo", rebinding_resolve)
    monkeypatch.setattr(socket.socket, "connect", only_local_fixture_connections)
    permissions = {"allowed_hosts": ["rebind.example.test"], "allow_private_network": False}
    try:
        captured = fetch_http(f"http://rebind.example.test:{port}/source", permissions, Budget())
    except Exception:
        captured = None
    assert not local_sources.requests, "DNS must not be resolved again into a private source after validation"
    assert captured is None, "No private fixture bytes may be returned through a false public permission"


def test_pinned_transport_retains_http_host_tls_sni_and_certificate_verification(monkeypatch):
    import httpcore
    import httpx
    import ssl
    from decision_recheck.transport import ScopedTransport
    resolved = []
    connected = []
    writes = []
    tls = []
    class FakeStream:
        response_sent = False
        def read(self, max_bytes, timeout=None):
            if self.response_sent: return b""
            self.response_sent = True
            return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"
        def write(self, data, timeout=None): writes.append(bytes(data))
        def close(self): pass
        def get_extra_info(self, name): return None
        def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            tls.append((server_hostname, ssl_context.verify_mode, ssl_context.check_hostname))
            return self
    def resolve(host, port, *args, **kwargs):
        resolved.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port))]
    def connect(self, host, port, timeout=None, local_address=None, socket_options=None):
        connected.append((host, port))
        return FakeStream()
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setattr(httpcore.SyncBackend, "connect_tcp", connect)
    permissions = {"allowed_hosts": ["origin.example.test"], "allow_private_network": True}
    with httpx.Client(transport=ScopedTransport(permissions), trust_env=False) as client:
        response = client.get("https://origin.example.test:9443/source")
    assert response.text == "ok"
    assert resolved == ["origin.example.test"]
    assert connected == [("127.0.0.1", 9443)], "TCP receives the validated numeric address, not the hostname"
    assert b"Host: origin.example.test:9443\r\n" in b"".join(writes)
    assert tls == [("origin.example.test", ssl.CERT_REQUIRED, True)]
