"""Minimal HTTP wrapper around emcc for the in-browser milestone runner.

POST /compile {"source": "<C++>"} -> {"ok": true, "js": "<ES6 module>"}
                                  -> {"ok": false, "diagnostics": "<stderr>"}
GET  /health                      -> {"status": "ok"}

Deliberately stdlib-only: the emsdk image ships Python 3, and this service
runs on the internal Docker network, reached only by the backend proxy.
"""

import json
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_SOURCE_BYTES = 200_000
COMPILE_TIMEOUT_S = 90

EMCC_ARGS = [
    "emcc",
    "main.cpp",
    "-o",
    "out.mjs",
    "-std=c++20",
    "-O1",
    "-I/opt/eigen",
    "-sMODULARIZE=1",
    "-sEXPORT_ES6=1",
    "-sSINGLE_FILE=1",
    "-sEXIT_RUNTIME=1",
    "-sENVIRONMENT=web,worker,node",
    # Scope panels read results straight out of linear memory; harness
    # functions are exported via EMSCRIPTEN_KEEPALIVE, not a flag.
    "-sEXPORTED_RUNTIME_METHODS=HEAPF32",
]


class Handler(BaseHTTPRequestHandler):
    def _reply(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path == "/health":
            self._reply(200, {"status": "ok"})
        else:
            self._reply(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        if self.path != "/compile":
            self._reply(404, {"detail": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_SOURCE_BYTES * 2:
            self._reply(413, {"detail": "request too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            source = payload["source"]
        except (json.JSONDecodeError, KeyError, TypeError):
            self._reply(400, {"detail": "body must be JSON with a 'source' string"})
            return
        if not isinstance(source, str) or not source.strip():
            self._reply(400, {"detail": "'source' must be a non-empty string"})
            return
        if len(source.encode()) > MAX_SOURCE_BYTES:
            self._reply(413, {"detail": "source too large"})
            return

        with tempfile.TemporaryDirectory() as workdir:
            (Path(workdir) / "main.cpp").write_text(source)
            try:
                proc = subprocess.run(
                    EMCC_ARGS,
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=COMPILE_TIMEOUT_S,
                )
            except subprocess.TimeoutExpired:
                self._reply(200, {"ok": False, "diagnostics": "compilation timed out"})
                return
            if proc.returncode != 0:
                self._reply(200, {"ok": False, "diagnostics": proc.stderr[-20_000:]})
                return
            js = (Path(workdir) / "out.mjs").read_text()
        self._reply(200, {"ok": True, "js": js})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} {fmt % args}")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
