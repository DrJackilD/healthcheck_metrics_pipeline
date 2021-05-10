import re
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from monitor.job import HealthcheckJobResult


class MetricsCollection(BaseModel):
    url: str
    response_time: float
    status_code: int
    regex_found: Optional[bool]


def collect_metrics(
    result: "HealthcheckJobResult", regex_pattern: Optional[str]
) -> MetricsCollection:
    """
    Function which interprets results of health check and produce metrics
    """
    metrics = MetricsCollection(
        url=result.url,
        response_time=(
            result.response_received_at - result.request_start_at
        ).total_seconds(),
        status_code=result.response_status,
    )
    if regex_pattern:
        pattern = re.compile(regex_pattern)
        metrics.regex_found = (
            pattern.search(result.response_content.decode()) is not None
        )
    return metrics
