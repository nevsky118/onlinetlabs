"""Local HTTP gateway for OpenClaw tests."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class OpenClawGatewayHandler(BaseHTTPRequestHandler):
    """Test HTTP gateway with a real TCP connection."""

    protocol_version = "HTTP/1.1"
    responses: list[dict] = []
    requests: list[dict] = []

    def do_POST(self):
        """Handle an OpenAI-compatible chat completions request."""
        length = int(self.headers.get("content-length", "0"))
        payload = self.rfile.read(length)
        self.__class__.requests.append(
            {
                "path": self.path,
                "authorization": self.headers.get("authorization"),
                "payload": payload,
                "client_address": self.client_address,
            }
        )
        body = self.__class__.responses.pop(0)
        encoded = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_):
        """Disable the noisy stderr log of the built-in HTTP server."""


class OpenClawGatewayServer:
    """Context manager for the test gateway on loopback."""

    def __init__(self, responses: list[dict]):
        self._responses = responses
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), OpenClawGatewayHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self):
        OpenClawGatewayHandler.responses = list(self._responses)
        OpenClawGatewayHandler.requests = []
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=1)

    @property
    def base_url(self) -> str:
        """Return the base URL of the test gateway."""
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    @property
    def requests(self) -> list[dict]:
        """Return the requests received by the test gateway."""
        return OpenClawGatewayHandler.requests


def completion_response(content: str, model: str = "openclaw") -> dict:
    """Build a valid chat completions response."""
    return {
        "id": "chatcmpl-test",
        "model": model,
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
    }
