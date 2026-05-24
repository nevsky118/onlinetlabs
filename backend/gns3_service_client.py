"""Async HTTP-клиент к gns3-service (provision/reset/teardown)."""

import httpx


class Gns3ServiceClient:
    """Async HTTP-клиент к gns3-service для управления сессиями студентов."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 60.0,
        internal_token: str | None = None,
    ):
        """Настраивает httpx-клиент с bearer-токеном и транспортными ретраями."""
        # Bearer-токен для /v1/exec/vtysh. Без него gns3-service отвергнет запрос.
        headers: dict[str, str] = {}
        if internal_token:
            headers["Authorization"] = f"Bearer {internal_token}"
        # Транспортные ретраи на уровне connection: httpx сам пересоберёт
        # сетевой коннект на ConnectError/ReadError до трёх раз. Логика
        # HTTP-ответов 5xx сюда не попадает, для них нужен retry в коде.
        transport = httpx.AsyncHTTPTransport(retries=3)
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers=headers,
            transport=transport,
        )

    async def create_session(self, user_id: str, template_project_id: str) -> dict:
        """Создать новую сессию из шаблонного проекта для пользователя."""
        resp = await self._client.post(
            "/sessions",
            json={"user_id": user_id, "lab_template_project_id": template_project_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def reset_project(self, gns3_service_session_id: str, template_project_id: str) -> dict:
        """Сбросить проект сессии к исходному состоянию шаблона."""
        resp = await self._client.post(
            f"/sessions/{gns3_service_session_id}/reset-project",
            json={"lab_template_project_id": template_project_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def delete_session(self, gns3_service_session_id: str) -> None:
        """Удалить сессию и освободить её ресурсы."""
        resp = await self._client.delete(f"/sessions/{gns3_service_session_id}")
        resp.raise_for_status()

    async def get_state(self, session_id: str) -> dict:
        """Получить текущее состояние сессии и её узлов."""
        resp = await self._client.get(f"/sessions/{session_id}/state")
        resp.raise_for_status()
        return resp.json()

    async def node_action(self, session_id: str, node_id: str, action: str) -> None:
        """Выполнить действие над одним узлом (start, stop и т.п.)."""
        resp = await self._client.post(f"/sessions/{session_id}/nodes/{node_id}/{action}")
        resp.raise_for_status()

    async def bulk_node_action(self, session_id: str, action: str) -> None:
        """Выполнить действие над всеми узлами сессии разом."""
        # Per-call timeout 180s: with backend-side semaphore (8 concurrent)
        # and ~10s per bulk-start on gns3-server, 50-student queue takes ~60s.
        # 180s gives 3x headroom for cold caches / heavier topologies.
        resp = await self._client.post(
            f"/sessions/{session_id}/nodes/{action}",
            timeout=180.0,
        )
        resp.raise_for_status()

    async def get_activity(
        self,
        session_id: str,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict:
        """Получить ленту активности сессии с курсорной пагинацией."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = await self._client.get(f"/sessions/{session_id}/activity", params=params)
        resp.raise_for_status()
        return resp.json()

    async def exec_vtysh(self, project_id: str, node_id: str, command: str) -> dict:
        """Выполнить vtysh-команду на docker-узле через gns3-service exec endpoint.

        Returns: `{stdout, stderr, exit_code}`.
        """
        resp = await self._client.post(
            "/v1/exec/vtysh",
            json={"project_id": project_id, "node_id": node_id, "command": command},
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        """Закрыть HTTP-клиент и его соединения."""
        await self._client.aclose()
