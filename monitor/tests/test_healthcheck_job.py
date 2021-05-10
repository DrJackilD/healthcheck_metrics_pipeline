import asyncio
from typing import Tuple
from unittest.mock import AsyncMock

import pytest
from aioresponses import aioresponses

from monitor.config import Settings
from monitor.job import healthcheck_job
from monitor.metrics import MetricsCollection
from monitor.monitor import JobParams


@pytest.mark.asyncio
async def test_healthcheck_job_success():
    settings = Settings()
    with aioresponses() as mocked_session:
        mocked_session.get("http://example.com", status=200, body="<h1>Hello</h1>")
        job_params = JobParams(
            url="http://example.com", schedule="* * * * *", body_regex="<h1>Hello</h1>"
        )
        lock = asyncio.Lock()
        on_result = AsyncMock()
        on_error = AsyncMock()
        await healthcheck_job(
            job_params=job_params,
            settings=settings,
            on_result=on_result,
            on_error=on_error,
            sync_lock=lock,
        )
        collected_metrics: MetricsCollection = on_result.call_args_list[0][0][0]
        assert [
            collected_metrics.status_code,
            collected_metrics.regex_found,
            collected_metrics.url,
        ] == [200, True, "http://example.com"]
        on_error.assert_not_called()


@pytest.mark.asyncio
async def test_healthcheck_job_failure():
    settings = Settings()
    with aioresponses() as mocked_session:
        expected_exception = ValueError("Test exception")
        mocked_session.get(
            "http://example.com",
            exception=expected_exception,
        )
        job_params = JobParams(
            url="http://example.com",
            schedule="* * * * *",
        )
        lock = asyncio.Lock()
        on_result = AsyncMock()
        on_error = AsyncMock()
        await healthcheck_job(
            job_params=job_params,
            settings=settings,
            on_result=on_result,
            on_error=on_error,
            sync_lock=lock,
        )
        on_result.assert_not_called()
        posted_on_exception: Tuple[JobParams, Exception] = on_error.call_args_list[0][0]
        assert posted_on_exception[0].url == "http://example.com"
        assert posted_on_exception[1] == expected_exception


@pytest.mark.asyncio
async def test_healthcheck_job_locked(monkeypatch):
    settings = Settings()
    job_params = JobParams(
        url="http://example.com",
        schedule="* * * * *",
    )
    lock = asyncio.Lock()
    on_result = AsyncMock()
    on_error = AsyncMock()
    monkeypatch.setattr(lock, "_locked", True)
    await healthcheck_job(
        job_params=job_params,
        settings=settings,
        on_result=on_result,
        on_error=on_error,
        sync_lock=lock,
    )
    on_result.assert_not_called()
    on_error.assert_not_called()
