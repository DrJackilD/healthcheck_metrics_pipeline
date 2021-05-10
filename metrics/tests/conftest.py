from unittest.mock import Mock

import pytest

from metrics.collectors.base import AbstractMetricsCollector
from metrics.config import Settings
from metrics.listener import MetricsListener


class KafkaConnectionMock:
    def __init__(self, messages=None):
        self.start_called = False
        self.stop_called = False
        self.messages = messages or []

    async def start(self):
        self.start_called = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return self.messages.pop()
        except IndexError:
            raise StopAsyncIteration

    async def stop(self):
        self.stop_called = True


@pytest.fixture
def listener(monkeypatch):
    settings = Settings(
        bootstrap_servers="localhost:9092",
        metrics_topics="wm_metrics",
        debug=True,
    )
    monkeypatch.setattr(
        MetricsListener,
        "_setup_connection",
        Mock(return_value=KafkaConnectionMock()),
    )
    metrics_listener = MetricsListener(
        settings, collectors=[Mock(spec=AbstractMetricsCollector)]
    )
    yield metrics_listener
