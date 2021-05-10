from unittest.mock import AsyncMock

import pytest

from monitor.loaders.kafka import KafkaLoader, KafkaLoaderSettings
from monitor.metrics import MetricsCollection


@pytest.mark.asyncio
async def test_kafka_loader(monkeypatch):
    settings = KafkaLoaderSettings(
        bootstrap_servers="localhost:9092",
        output_topic="wh_metrics",
        ssl_auth=False,
    )
    loader = KafkaLoader(settings)
    mocked_connection = AsyncMock()
    monkeypatch.setattr(loader, "_conn", mocked_connection)
    metrics = MetricsCollection(
        url="http://example.com", status_code=200, response_time=1
    )
    await loader.load(metrics)
    mocked_connection.send_and_wait.assert_called_once_with(
        settings.output_topic, metrics.json().encode()
    )
