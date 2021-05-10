from unittest.mock import AsyncMock, Mock

import pytest
from aiocron import Cron

from monitor.config import Settings
from monitor.loaders.base import AbstractLoader
from monitor.monitor import HealthMonitor


@pytest.fixture
def monitor(monkeypatch):
    settings = Settings()
    monkeypatch.setattr(
        HealthMonitor, "_parse_schedule", Mock(return_value=[AsyncMock(spec=Cron)])
    )
    monitor = HealthMonitor(settings, loaders=[Mock(spec=AbstractLoader)])
    yield monitor
