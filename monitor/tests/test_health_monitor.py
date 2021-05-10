from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

import pytest

from monitor.metrics import MetricsCollection
from monitor.monitor import HealthMonitor


@pytest.mark.asyncio
async def test_health_monitor(monitor: HealthMonitor):
    await monitor.start()
    monitor.jobs[0].start.assert_called_once()
    metrics = MetricsCollection(
        url="http://example.com", response_time=1, status_code=200, regex_found=True
    )
    await monitor.publish(metrics)
    monitor.loaders[0].load.assert_called_once_with(metrics)  # type: ignore
