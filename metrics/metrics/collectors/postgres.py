import logging
from ssl import create_default_context
from typing import Optional

import asyncpg
from pydantic import BaseSettings, PostgresDsn

from metrics.metrics import MetricsCollection
from metrics.utils import BackoffPolicy

from .base import AbstractMetricsCollector, ensure_connected

logger = logging.getLogger(__name__)


class PostgresSettings(BaseSettings):

    dsn: PostgresDsn
    """Connection string for PostgreSQL"""

    table: str = "metrics"
    """Name of the table to write metrics"""

    ssl: bool = False
    """Establish connection with SSL"""

    class Config:
        env_prefix = "wm_postgres_"


class PostgresMetricsCollector(AbstractMetricsCollector):
    def __init__(self, settings: Optional[PostgresSettings] = None):
        self.settings = settings or PostgresSettings()
        self.backoff_policy = BackoffPolicy(3, 5, 5)
        self._conn: Optional[asyncpg.Connection] = None

    async def connect(self):
        if self._conn is None:
            ssl_context = None
            if self.settings.ssl:
                ssl_context = create_default_context(cafile="init/postgres/ca.pem")
            self._conn = await self.backoff_policy.run(
                asyncpg.connect, self.settings.dsn, ssl=ssl_context
            )
            logger.debug("Connected to database")

    @ensure_connected
    async def start(self):
        assert self._conn is not None, "Configuration error"

        logger.info("Start PostgreSQL metrics collector")
        await self._create_tables()

    @ensure_connected
    async def collect(self, metrics: MetricsCollection):
        assert self._conn is not None, "Configuration error"

        logger.debug(f"Received {metrics!r}")
        await self._insert_metrics(metrics)

    async def shutdown(self):
        if self._conn:
            await self._conn.close(timeout=5)
        logger.info("Postgres collector shutdown completed")

    async def _create_tables(self):
        assert self._conn is not None, "Configuration error"

        logger.debug("Create tables")
        stmt = f"""CREATE TABLE IF NOT EXISTS {self.settings.table} (
              id SERIAL PRIMARY KEY,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              url VARCHAR(255) NOT NULL DEFAULT '',
              response_time FLOAT NOT NULL DEFAULT 0,
              status_code INTEGER NOT NULL DEFAULT 0,
              regex_found BOOLEAN
            );
            CREATE INDEX IF NOT EXISTS url_idx ON {self.settings.table}(url);
            """
        await self._conn.execute(stmt, timeout=10)

    async def _insert_metrics(self, metrics: MetricsCollection):
        assert self._conn is not None, "Configuration error"

        stmt = f"INSERT INTO {self.settings.table}(url, response_time, status_code, regex_found) VALUES($1, $2, $3, $4)"
        await self._conn.execute(
            stmt,
            metrics.url,
            metrics.response_time,
            metrics.status_code,
            metrics.regex_found,
            timeout=10,
        )
