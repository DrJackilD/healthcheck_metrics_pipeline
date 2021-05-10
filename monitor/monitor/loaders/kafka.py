import logging
from typing import Optional

import aiokafka
from aiokafka.helpers import create_ssl_context
from pydantic import BaseSettings

from monitor.metrics import MetricsCollection
from monitor.utils import BackoffPolicy

from .base import AbstractLoader, ensure_connected

logger = logging.getLogger(__name__)


class KafkaLoaderSettings(BaseSettings):
    bootstrap_servers: str
    """List of comma-separated addresses of bootstrap servers"""

    output_topic: str
    """Kafka topic to loads metrics"""

    ssl_auth: bool = False
    """Enable SSL authentication mechanism for Kafka."""

    class Config:
        env_prefix = "wh_kafka_"


class KafkaLoader(AbstractLoader):
    """
    Loader to upload metrics to target Kafka topic
    """

    def __init__(self, settings: Optional[KafkaLoaderSettings] = None):
        self._settings = settings or KafkaLoaderSettings()
        self._conn: Optional[aiokafka.AIOKafkaProducer] = None
        # Kafka on fresh start could take up to 30 seconds to properly setup
        # so let's expect this in our backoff policy
        self._backoff_policy = BackoffPolicy(3, 10, 10)

    async def connect(self):
        if self._conn is None:
            if self._settings.ssl_auth:
                ssl_context = create_ssl_context(
                    cafile="init/kafka/ca.pem",
                    certfile="init/kafka/service.cert",
                    keyfile="init/kafka/service.key",
                )
                self._conn = aiokafka.AIOKafkaProducer(
                    bootstrap_servers=self._settings.bootstrap_servers,
                    ssl_context=ssl_context,
                    security_protocol="SSL",
                )
            else:
                self._conn = aiokafka.AIOKafkaProducer(
                    bootstrap_servers=self._settings.bootstrap_servers,
                )
            await self._backoff_policy.run(self._conn.start)
            logger.debug(
                f"Successfully established connection to Kafka on {self._settings.bootstrap_servers}"
            )

    @ensure_connected
    async def load(self, result: MetricsCollection):
        assert self._conn is not None, "Kafka connection is not initialized"
        await self._conn.send_and_wait(
            self._settings.output_topic, result.json().encode()
        )

    async def shutdown(self):
        if self._conn is not None:
            await self._conn.stop()
        logger.debug("KafkaLoader shutdown completed")
