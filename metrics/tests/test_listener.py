import pytest

from metrics.listener import MetricsListener
from metrics.metrics import MetricsCollection


@pytest.mark.asyncio
async def test_listener(listener: MetricsListener):
    metrics = [
        MetricsCollection(url="https://example.com", status_code=200, response_time=3)
        .json()
        .encode(),
        MetricsCollection(url="https://google.com", status_code=200, response_time=1)
        .json()
        .encode(),
        MetricsCollection(
            url="https://aiven.io",
            status_code=200,
            response_time=1,
            regex_found=True,
        )
        .json()
        .encode(),
    ]

    listener._conn.messages = metrics
    await listener.start()
    listener.collectors[0].collect.assert_has_calls(metrics)  # type: ignore
    await listener.shutdown()
    listener.collectors[0].shutdown.assert_called_once()  # type: ignore
