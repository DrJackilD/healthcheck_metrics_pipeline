from abc import ABC, abstractmethod
from functools import wraps

from metrics.metrics import MetricsCollection


def ensure_connected(func):
    """Decorator to mark some method as waited for connection before start"""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        await self.connect()
        return await func(self, *args, **kwargs)

    return wrapper


class AbstractMetricsCollector(ABC):
    """
    This class provide abstract representation
    of any classes which want to work as metrics collector
    """

    @abstractmethod
    async def start(self):
        """
        Method called on each start of metrics listener
        """
        pass

    @abstractmethod
    async def collect(self, metrics: MetricsCollection):
        """
        Method called for each collected metric from Kafka
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """
        Shutdown collector, closes connections, etc.
        """
        pass
