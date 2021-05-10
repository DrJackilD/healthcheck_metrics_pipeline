import asyncio
import logging

from monitor.config import Settings
from monitor.loaders.kafka import KafkaLoader
from monitor.log import setup_logging
from monitor.monitor import HealthMonitor

logger = logging.getLogger(__name__)

# General event which indicate that shutdown completed
shutdown_completed = asyncio.Event()


async def main(shutdown: asyncio.Event):
    settings = Settings()

    setup_logging(settings)

    logger.info("Start Health Monitor")

    monitor = HealthMonitor(settings, [KafkaLoader()])
    await monitor.start()

    await shutdown.wait()

    logger.info("Shutdown triggered, stop the monitor")
    await monitor.shutdown()
    shutdown_completed.set()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()
    try:
        loop.run_until_complete(main(shutdown_event))
    except KeyboardInterrupt:
        shutdown_event.set()
        loop.run_until_complete(shutdown_completed.wait())
