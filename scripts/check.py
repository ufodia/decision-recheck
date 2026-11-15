"""Run the complete suite with an owned loopback preview and guaranteed cleanup."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import sys
import threading


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    handler = partial(QuietHandler, directory=str(project / "site"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    environment = os.environ.copy()
    environment["DRC_DEMO_URL"] = "http://127.0.0.1:" + str(server.server_port)
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", *sys.argv[1:]], cwd=project, env=environment, check=False)
        return result.returncode
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())
