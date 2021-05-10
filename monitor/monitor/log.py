import logging

from monitor import config


def setup_logging(settings: config.Settings):
    """
    Setup logging configuration for application
    :param settings: application settings
    """
    logging.basicConfig(
        format="%(asctime)s %(name)s [%(levelname)s]: %(message)s",
        level=logging.DEBUG if settings.debug else logging.INFO,
    )
