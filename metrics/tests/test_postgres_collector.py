from unittest.mock import AsyncMock

import pytest

from metrics.collectors.postgres import PostgresMetricsCollector, PostgresSettings
from metrics.metrics import MetricsCollection


@pytest.mark.asyncio
async def test_postgres_collector():
    settings = PostgresSettings(
        dsn="postgres://postgres:postgres@localhost:5432/testdb",
        table="test_metrics",
        ssl=False,
    )
    collector = PostgresMetricsCollector(settings)
    collector._conn = AsyncMock()
    await collector.start()
    collector._conn.execute.assert_called_once_with(
        f"""CREATE TABLE IF NOT EXISTS {settings.table} (
              id SERIAL PRIMARY KEY,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              url VARCHAR(255) NOT NULL DEFAULT '',
              response_time FLOAT NOT NULL DEFAULT 0,
              status_code INTEGER NOT NULL DEFAULT 0,
              regex_found BOOLEAN
            );
            CREATE INDEX IF NOT EXISTS url_idx ON {settings.table}(url);
            """,
        timeout=10,
    )
    metrics = MetricsCollection(
        url="https://example.com", status_code=200, response_time=3
    )
    await collector.collect(metrics)
    collector._conn.execute.assert_called_with(
        f"INSERT INTO {settings.table}(url, response_time, status_code, regex_found) VALUES($1, $2, $3, $4)",
        metrics.url,
        metrics.response_time,
        metrics.status_code,
        metrics.regex_found,
        timeout=10,
    )
