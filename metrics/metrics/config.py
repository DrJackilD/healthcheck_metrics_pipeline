from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Various settings parameters for WH Metrics application
    """

    bootstrap_servers: str
    """List of comma-separated addresses of bootstrap servers"""

    metrics_topics: str
    """List of comma-separated topic to listen for new metrics"""

    kafka_ssl_auth: bool = False
    """Enable SSL authentication mechanism for Kafka."""

    debug: bool = False
    """Indicate is this node should work in debug mode"""

    class Config:
        env_prefix = "wm_"
