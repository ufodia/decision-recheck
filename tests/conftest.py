"""Owned, local-only HTTP fixtures for public runner integration tests."""
from __future__ import annotations
import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
import pytest

@dataclass
class LocalSources:
    responses: dict[str, tuple[int, str, bytes, dict[str, str]]] = field(default_factory=dict)
    requests: list[tuple[str, str]] = field(default_factory=list)
    base_url: str = ""
    def json(self, path: str, value: Any, status: int = 200) -> None:
        self.responses[path] = (status, "application/json", json.dumps(value).encode(), {})
    def html(self, path: str, value: str, status: int = 200) -> None:
        self.responses[path] = (status, "text/html; charset=utf-8", value.encode(), {})
    def redirect(self, path: str, location: str) -> None:
        self.responses[path] = (302, "text/plain", b"", {"Location": location})

@pytest.fixture
def local_sources():
    """Serve mutable synthetic sources on a fresh loopback port for each test."""
    state = LocalSources()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            state.requests.append(("GET", self.path))
            status, media_type, body, headers = state.responses.get(self.path, (404, "text/plain", b"Not found", {}))
            self.send_response(status)
            self.send_header("Content-Type", media_type)
            self.send_header("Content-Length", str(len(body)))
            for name, value in headers.items(): self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)
        def deny_write(self):
            state.requests.append((self.command, self.path))
            self.send_error(405, "Synthetic source server never accepts mutations")
        do_POST = do_PUT = do_PATCH = do_DELETE = deny_write
        def log_message(self, *_args): pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state.base_url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try: yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
