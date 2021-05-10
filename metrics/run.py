import asyncio
import logging

from metrics.collectors.postgres import PostgresMetricsCollector
from metrics.config import Settings
from metrics.listener import MetricsListener
from metrics.log import setup_logging

logger = logging.getLogger(__name__)

# General event which indicate that shutdown completed
shutdown_completed = asyncio.Event()


async def main(loop: asyncio.AbstractEventLoop, shutdown: asyncio.Event):
    logger.info("Start Health Monitor")
    settings = Settings()
    setup_logging(settings)
    listener = MetricsListener(settings, [PostgresMetricsCollector()])
    listener_task = loop.create_task(listener.start())
    await shutdown.wait()
    logger.info("Shutdown triggered, stop the metrics listener")
    listener_task.cancel()
    await listener.shutdown()
    shutdown_completed.set()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()
    try:
        loop.run_until_complete(main(loop, shutdown_event))
    except KeyboardInterrupt:
        shutdown_event.set()
        loop.run_until_complete(shutdown_completed.wait())
