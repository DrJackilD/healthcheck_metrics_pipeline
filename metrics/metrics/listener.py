import asyncio
import logging
import typing as t

import aiokafka
from aiokafka.helpers import create_ssl_context

from .collectors.base import AbstractMetricsCollector
from .config import Settings
from .metrics import MetricsCollection
from .utils import BackoffPolicy

logger = logging.getLogger(__name__)


class MetricsListener:
    """
    This is a main class for WH Metrics application.
    It listens for results in Kafka topic and sends them to
    list of defined collectors
    """

    def __init__(
        self,
        settings: Settings,
        collectors: t.List[AbstractMetricsCollector],
    ):
        self.settings = settings
        self.collectors = collectors
        self._conn = self._setup_connection()
        self.backoff_policy = BackoffPolicy(3, 10, 10)

    async def start(self):
        """
        Starts listen for new metrics.
        """
        try:
            start_tasks = [
                asyncio.wait_for(collector.start(), 10) for collector in self.collectors
            ]
            await asyncio.gather(*start_tasks)
            await self.backoff_policy.run(self._conn.start)
            async for raw_message in self._conn:
                raw_message: aiokafka.ConsumerRecord[bytes]
                try:
                    metrics = MetricsCollection.parse_raw(raw_message.value)
                    coros = [
                        collector.collect(metrics) for collector in self.collectors
                    ]
                    await asyncio.gather(*coros)
                except Exception as e:
                    logger.error(
                        f"Failed to parse raw metrics {raw_message[:20]!r}", exc_info=e
                    )
        except asyncio.CancelledError:
            logger.info("MetricsListener.start canceled, stop listen for new metrics")

    async def shutdown(self):
        await self._conn.stop()
        coros = [
            asyncio.wait_for(collector.shutdown(), 10) for collector in self.collectors
        ]
        await asyncio.gather(*coros)
        logger.info("Shutdown completed")

    def _setup_connection(self) -> aiokafka.AIOKafkaConsumer:
        if self.settings.kafka_ssl_auth:
            ssl_context = create_ssl_context(
                cafile="init/kafka/ca.pem",
                certfile="init/kafka/service.cert",
                keyfile="init/kafka/service.key",
            )
            connection = aiokafka.AIOKafkaConsumer(
                *self.settings.metrics_topics.split(","),
                bootstrap_servers=self.settings.bootstrap_servers,
                ssl_context=ssl_context,
                security_protocol="SSL",
            )
        else:
            connection = aiokafka.AIOKafkaConsumer(
                *self.settings.metrics_topics.split(","),
                bootstrap_servers=self.settings.bootstrap_servers,
            )
        return connection
