from abc import ABC, abstractmethod
from functools import wraps

from monitor.metrics import MetricsCollection


def ensure_connected(func):
    """Decorator to mark some method as waited for connection before start"""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        await self.connect()
        return await func(self, *args, **kwargs)

    return wrapper


class AbstractLoader(ABC):
    """
    Interface for all classes which want to works as a metrics loader
    """

    @abstractmethod
    async def load(self, metric: MetricsCollection):
        """
        Loads metrics
        :param metric: metrics to load
        """
        pass

    @abstractmethod
    async def connect(self):
        """
        Calls to establish internal loader's connections and make some other preparations
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """
        Using on graceful shutdown to make cleanup works
        """
        pass
