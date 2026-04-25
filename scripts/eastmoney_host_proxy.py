#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = os.getenv("EASTMONEY_PROXY_HOST", "0.0.0.0")
PORT = int(os.getenv("EASTMONEY_PROXY_PORT", "8899"))
CURL_BIN = shutil.which("curl") or "curl"


def fetch_with_curl(url: str, params: dict, headers: dict, timeout: int = 20):
    full_url = url
    if params:
        from urllib.parse import urlencode
        # Eastmoney is sensitive to encoded market-selector params like
        # fs=m:0+t:6,m:0+t:80, so keep commas/colons/pluses readable.
        full_url = f"{url}?{urlencode(params, safe=':,+')}"

    cmd = [
        CURL_BIN,
        "--silent",
        "--show-error",
        "--location",
        "--compressed",
        "--max-time",
        str(timeout),
    ]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.append(full_url)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"curl exit code {result.returncode}")
    return json.loads(result.stdout)


class Handler(BaseHTTPRequestHandler):
    server_version = "EastmoneyHostProxy/1.0"

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if self.path != "/fetch":
            self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception as exc:
            self._send_json({"error": f"invalid json: {exc}"}, status=HTTPStatus.BAD_REQUEST)
            return

        url = payload.get("url", "")
        params = payload.get("params", {}) or {}
        headers = payload.get("headers", {}) or {}
        if not url.startswith("https://") or "eastmoney.com" not in url:
            self._send_json({"error": "only eastmoney https urls are allowed"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            data = fetch_with_curl(url=url, params=params, headers=headers, timeout=int(payload.get("timeout", 20)))
            self._send_json({"ok": True, "data": data})
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"eastmoney host proxy listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
