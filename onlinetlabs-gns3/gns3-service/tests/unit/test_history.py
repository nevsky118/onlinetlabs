import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.history]


class TestHistoryListener:
    @autotests.num("450")
    @autotests.external_id("a1b2c3d4-0001-4aaa-bbbb-450000000001")
    @autotests.name("GNS3 History: _parse_event извлекает данные из WS")
    def test_parse_event(self):
        from src.history import HistoryListener

        listener = HistoryListener.__new__(HistoryListener)
        raw = json.dumps({"event": "node.updated", "project_id": "pid-1", "node_id": "n1"})
        result = listener._parse_event(raw)
        assert result["event_type"] == "node.updated"
        assert result["project_id"] == "pid-1"
        assert result["component_id"] == "n1"

    @autotests.num("451")
    @autotests.external_id("a1b2c3d4-0002-4aaa-bbbb-451000000001")
    @autotests.name("GNS3 History: _persist_event сохраняет в БД")
    async def test_persist_event(self):
        from src.history import HistoryListener

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        listener = HistoryListener.__new__(HistoryListener)
        listener._session_factory = mock_session_factory
        sid = uuid.uuid4()
        listener._project_to_session = {"pid-1": sid}

        await listener._persist_event({
            "event_type": "node.updated",
            "project_id": "pid-1",
            "component_id": "node-1",
            "data": {"status": "started"},
        })
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
