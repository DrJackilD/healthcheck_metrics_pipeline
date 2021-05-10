import asyncio
import datetime
import logging
import typing as t

from aiohttp import ClientTimeout
from aiohttp.client import ClientSession
from pydantic import BaseModel

from monitor.config import Settings
from monitor.metrics import MetricsCollection, collect_metrics

if t.TYPE_CHECKING:
    from monitor.monitor import JobParams

logger = logging.getLogger(__name__)


class HealthcheckJobResult(BaseModel):
    """
    Class to keep request result
    """

    url: str
    request_start_at: datetime.datetime
    response_received_at: datetime.datetime
    response_headers: dict
    response_content: bytes
    response_status: int


async def healthcheck_job(
    job_params: "JobParams",
    on_result: t.Callable[[MetricsCollection], t.Awaitable[None]],
    on_error: t.Callable[["JobParams", Exception], t.Awaitable[None]],
    sync_lock: asyncio.Lock,
    settings: Settings,
):
    """
    Makes request to target url, produce metrics and send them to output queue
    :param job_params: contains JobParams instance with details about this job
    :param on_result: callback function to call with results
    :param on_error: callback function to call with any errors
    :param sync_lock: lock to keep one instance of each health check job at a time
    :param settings: instance of application settings
    """
    if sync_lock.locked():
        logger.debug(f"Health check locked for {job_params}. Skipping.")
        return

    async with sync_lock:
        start_at = datetime.datetime.utcnow()
        try:
            async with ClientSession(
                timeout=ClientTimeout(total=settings.request_timeout)
            ) as session:
                async with session.get(job_params.url) as response:
                    result = HealthcheckJobResult(
                        url=job_params.url,
                        request_start_at=start_at,
                        response_received_at=datetime.datetime.utcnow(),
                        response_headers=response.headers,
                        response_content=await response.read(),
                        response_status=response.status,
                    )
            metrics = collect_metrics(result, regex_pattern=job_params.body_regex)
            await on_result(metrics)
        except Exception as e:
            await on_error(job_params, e)
