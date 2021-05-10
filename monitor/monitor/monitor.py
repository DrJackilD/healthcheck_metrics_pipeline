import asyncio
import logging
import typing as t

import yaml
from aiocron import Cron
from pydantic import BaseModel, HttpUrl

from .config import Settings
from .job import healthcheck_job
from .loaders.base import AbstractLoader
from .metrics import MetricsCollection

logger = logging.getLogger(__name__)


class JobParams(BaseModel):
    """
    Simple model to keep data from yaml schedule
    and make some minimal type validation
    """

    url: HttpUrl
    schedule: str
    body_regex: t.Optional[str]


class HealthMonitor:
    """
    This is a main class for WH Monitor application.
    It collect results from periodic checks
    and pass this results to loaders
    """

    def __init__(
        self,
        settings: Settings,
        loaders: t.List[AbstractLoader],
    ):
        self.settings = settings
        self.loaders = loaders
        self.jobs = self._parse_schedule()

    async def start(self):
        """
        Starts all scheduled jobs
        """
        for j in self.jobs:
            j.start()
        logger.info("Jobs are scheduled")

    async def shutdown(self):
        """
        Stops all cron jobs and loaders and do any other required tasks for shutdown
        """
        for job in self.jobs:
            job.stop()
        coros = [asyncio.wait_for(loader.shutdown(), 10) for loader in self.loaders]
        await asyncio.gather(*coros)
        logger.info("Shutdown completed")

    async def publish(self, metrics: MetricsCollection):
        """
        Method used by health check jobs to publish their results
        """
        loads = [loader.load(metrics) for loader in self.loaders]
        await asyncio.gather(*loads)

    async def on_error_callback(self, job_params: JobParams, exc: Exception):
        """
        Method to post any exceptions during health check
        """
        logger.error(f"Exception during job {job_params.url}", exc_info=exc)

    def _parse_schedule(self) -> t.List[Cron]:
        """
        Parse yaml schedule and create periodic jobs for each entry
        :return: list of prepared Cron jobs for each entry in the schedule
        """
        jobs = []
        with open("schedule.yaml") as f:
            schedule = yaml.safe_load(f.read())
            logger.info(f"Total {len(schedule)} jobs parsed")
            for entry in schedule:
                job_params = JobParams(**entry)
                cron = Cron(
                    job_params.schedule,
                    func=healthcheck_job,
                    args=(
                        job_params,
                        self.publish,
                        self.on_error_callback,
                        asyncio.Lock(),
                        self.settings,
                    ),
                )
                jobs.append(cron)
        return jobs
