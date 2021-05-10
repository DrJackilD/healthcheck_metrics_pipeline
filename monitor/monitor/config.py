from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Various settings parameters for WH Monitor application
    """

    request_timeout: int = 20
    """Request timeout (in seconds)"""

    debug: bool = False
    """Indicate is this node should work in debug mode"""

    class Config:
        env_prefix = "wh_"
