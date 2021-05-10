from typing import Optional

from pydantic import BaseModel


class MetricsCollection(BaseModel):
    url: str
    response_time: float
    status_code: int
    regex_found: Optional[bool]
