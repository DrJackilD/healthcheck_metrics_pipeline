import asyncio
import logging
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)


class BackoffPolicy:
    """
    Helper to retry async execution with retries and increasing delays
    """

    def __init__(self, max_retries: int, start_delay: int, delay_step: int):
        self.max_retries = max_retries
        self.start_delay = start_delay
        self.delay_step = delay_step

    async def run(self, func: Callable[..., Awaitable[None]], *args, **kwargs):
        attempt = 1
        delay = self.start_delay
        while attempt <= self.max_retries:
            logger.debug(f"Try {attempt}/{self.max_retries} for {func}")
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Error during run {func}. retry after {delay} seconds", exc_info=e
                )
                await asyncio.sleep(delay)
                delay += self.delay_step
                attempt += 1
        else:
            logger.error(f"Max retries exceed with {func}, cannot recover")
            raise MaxRetriesExceeded(f"Max retries exceed with {func}, cannot recover")


class MaxRetriesExceeded(Exception):
    pass
