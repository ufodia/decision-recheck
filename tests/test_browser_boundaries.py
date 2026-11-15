"""Small real-browser suite for task boundaries; no personal browser profiles."""
from __future__ import annotations
from pathlib import Path
import pytest
from decision_recheck import browser as browser_module
from decision_recheck.models import load_brief
from decision_recheck.policy import Budget
from test_saas_scenarios import brief_for


@pytest.fixture
def installed_browser(monkeypatch):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        bundled = Path(p.chromium.executable_path)
    if bundled.exists(): return
    candidates = [Path("C:/Program Files/Google/Chrome/Application/chrome.exe"), Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"), Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")]
    executable = next((p for p in candidates if p.exists()), None)
    if executable is None: pytest.skip("No installed browser available; run playwright install chromium for this suite")
    monkeypatch.setattr(browser_module, "_launch", lambda p, **kwargs: p.chromium.launch(headless=True, executable_path=str(executable), timeout=kwargs.get("timeout_ms", 30000)))


def browser_brief(server):
    brief = brief_for()
    brief["permissions"] = {"allowed_hosts": ["127.0.0.1"], "allow_private_network": True, "allow_test_writes": False, "allowed_actions": ["read", "assert_text"]}
    return load_brief(brief)


def attempt(server, tmp_path, brief, steps, *, path="/task", task_id="attempt"):
    return browser_module.run_task({"id": task_id, "title": "Synthetic task", "url": server.base_url + path, "steps": steps}, brief, Budget(brief["limits"]), tmp_path)


def test_404_task_page_cannot_be_reported_as_passed(tmp_path, local_sources, installed_browser):
    local_sources.html("/task", "<h1>Not found</h1>", status=404)
    result, artifacts = attempt(local_sources, tmp_path, browser_brief(local_sources), [{"action": "read", "selector": "body"}])
    assert result["execution"] in {"blocked", "interrupted", "not_tested"}
    assert result["execution"] != "passed"


def test_missing_selector_is_incomplete_not_a_product_failure(tmp_path, local_sources, installed_browser):
    local_sources.html("/task", "<h1>Sign in is required for this view</h1>")
    result, artifacts = attempt(local_sources, tmp_path, browser_brief(local_sources), [{"action": "assert_text", "selector": "#missing", "value": "CSV export"}])
    assert result["execution"] == "blocked"
    assert artifacts, "Incomplete attempts still need an event record"


def test_contexts_do_not_share_local_storage(tmp_path, local_sources, installed_browser):
    local_sources.html("/first", '<div id="state">first</div><script>localStorage.setItem("private-task-marker","present")</script>')
    local_sources.html("/second", '<div id="state">clean</div><script>if(localStorage.getItem("private-task-marker"))document.getElementById("state").textContent="leaked"</script>')
    brief = browser_brief(local_sources)
    first, _ = attempt(local_sources, tmp_path / "first", brief, [{"action": "assert_text", "selector": "#state", "value": "first"}], path="/first", task_id="first")
    second, _ = attempt(local_sources, tmp_path / "second", brief, [{"action": "assert_text", "selector": "#state", "value": "clean"}], path="/second", task_id="second")
    assert first["execution"] == "passed", first
    assert second["execution"] == "passed", second


def test_page_initiated_post_is_blocked_in_read_only_mode(tmp_path, local_sources, installed_browser):
    local_sources.html("/task", '<div id="state">safe source</div><script>fetch("/mutation",{method:"POST",body:"synthetic"}).catch(()=>{})</script>')
    result, _ = attempt(local_sources, tmp_path, browser_brief(local_sources), [{"action": "assert_text", "selector": "#state", "value": "safe source"}])
    assert result["execution"] == "passed", result
    assert not any(method != "GET" for method, _path in local_sources.requests)


def test_click_cannot_send_a_message_without_test_write_permission(tmp_path, local_sources, installed_browser):
    local_sources.html("/task", '<form action="/message" method="post"><button id="send">Send support message</button></form>')
    brief = browser_brief(local_sources)
    brief["permissions"]["allowed_actions"].append("click")
    result, _ = attempt(local_sources, tmp_path, brief, [{"action": "click", "selector": "#send"}])
    assert result["execution"] == "blocked"
    assert not any(method == "POST" for method, _path in local_sources.requests)

@pytest.mark.parametrize("steps", [[], [{"action": "read", "selector": "body"}]])
def test_task_without_assertion_does_not_claim_a_verified_pass(tmp_path, local_sources, installed_browser, steps):
    local_sources.html("/task", "<h1>A page loaded, but no success condition was declared</h1>")
    result, _ = attempt(local_sources, tmp_path, browser_brief(local_sources), steps)
    assert result["execution"] != "passed"


def test_password_target_is_checked_from_dom_after_navigation_actions(tmp_path, local_sources, installed_browser):
    local_sources.html("/task", '<button id="reveal" onclick="document.getElementById(\'field\').type=\'password\'">Reveal form</button><input id="field" type="text">')
    brief = browser_brief(local_sources)
    brief["permissions"].update({"allow_test_writes": True, "allowed_actions": ["read", "assert_text", "click", "fill"]})
    result, _ = attempt(local_sources, tmp_path, brief, [{"action": "click", "selector": "#reveal"}, {"action": "fill", "selector": "#field", "value": "synthetic-not-a-real-credential"}])
    assert result["execution"] == "blocked"
    assert not any(step.get("action") == "fill" for step in result["steps"])


def test_websocket_cannot_bypass_read_only_host_allowlist(tmp_path, local_sources, installed_browser):
    port = local_sources.base_url.rsplit(":", 1)[1]
    local_sources.html("/task", f'''<div id="result"></div><script>
const socket = new WebSocket("ws://localhost:{port}/unapproved-socket");
const done = () => {{ if (!document.getElementById("socket-done")) {{const proof=document.createElement("span");proof.id="socket-done";proof.textContent="Core task passed";document.getElementById("result").append(proof);}} }};
socket.onerror=done;socket.onclose=done;
</script>''')
    result, _ = attempt(local_sources, tmp_path, browser_brief(local_sources), [{"action": "assert_text", "selector": "#socket-done", "value": "Core task passed"}])
    assert result["execution"] == "passed", result
    assert ("GET", "/unapproved-socket") not in local_sources.requests, "The unapproved host must receive no WebSocket upgrade handshake"


def test_html_source_reader_also_blocks_websocket_handshakes(tmp_path, installed_browser):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    from decision_recheck.browser import read_html_source
    finished = threading.Event()
    handshakes = []
    server = None
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/unapproved-socket":
                handshakes.append(self.path)
                self.send_error(400)
                return
            if self.path == "/event":
                finished.set()
                body, media = b"observed", "text/plain"
            elif self.path == "/wait.js":
                if not finished.wait(timeout=5):
                    self.send_error(504)
                    return
                body, media = b"/* websocket lifecycle observed */", "application/javascript"
            else:
                body = f'''<script>
const socket = new WebSocket("ws://localhost:{server.server_port}/unapproved-socket");
const done = () => fetch("/event").catch(()=>{{}});
socket.onerror=done;socket.onclose=done;
</script><script src="/wait.js"></script><p id="proof">Core source loaded</p>'''.encode()
                media = "text/html"
            self.send_response(200)
            self.send_header("Content-Type", media)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_): pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        brief = brief_for()
        brief["permissions"].update({"allowed_hosts": ["127.0.0.1"], "allow_private_network": True})
        source = {"id": "html-proof", "format": "html", "url": f"http://127.0.0.1:{server.server_port}/source", "fields": {"proof": "#proof"}}
        captured = read_html_source(source, brief, Budget(brief["limits"]))
        assert captured["values"]["proof"] == "Core source loaded"
        assert finished.is_set(), "Positive control must observe the WebSocket lifecycle"
        assert handshakes == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
