"""Локальный HTTP Gateway для тестов OpenClaw."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class OpenClawGatewayHandler(BaseHTTPRequestHandler):
    """Тестовый HTTP Gateway с настоящим TCP-соединением."""

    protocol_version = "HTTP/1.1"
    responses: list[dict] = []
    requests: list[dict] = []

    def do_POST(self):
        """Обработать OpenAI-совместимый chat completions запрос."""
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
        """Отключить шумный stderr-лог встроенного HTTP server."""


class OpenClawGatewayServer:
    """Контекстный менеджер тестового Gateway на loopback."""

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
        """Вернуть базовый URL тестового Gateway."""
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    @property
    def requests(self) -> list[dict]:
        """Вернуть запросы, полученные тестовым Gateway."""
        return OpenClawGatewayHandler.requests


def completion_response(content: str, model: str = "openclaw") -> dict:
    """Собрать валидный chat completions ответ."""
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
