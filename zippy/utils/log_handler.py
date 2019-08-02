"""Custom Log Handler."""
import logging
import pathlib

from logging.config import dictConfig
from logging.handlers import RotatingFileHandler

from zippy.utils import config


class ZippyDisplayFileLogHandler(RotatingFileHandler):
    """Custom log handler that saves log to output dir even if called from any dir."""

    def __init__(self, filename, *args, **kwargs):
        log_dir = pathlib.Path(__file__).parents[2] / "output" / "logs" / "display"
        super().__init__(log_dir / filename, *args, **kwargs)


class ZippyFileLogHandler(RotatingFileHandler):
    """Custom log handler that saves log to output dir even if called from any dir."""

    def __init__(self, filename, *args, **kwargs):
        log_dir = pathlib.Path(__file__).parents[2] / "output" / "logs"
        super().__init__(log_dir / filename, *args, **kwargs)


def get_logger(name: str) -> logging.Logger:
    """Return logger if in config, else use basic console."""
    logger = logging.getLogger(name)
    try:
        conf = config.get_config("logger")
    except KeyError:
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
    else:
        logger = logging.getLogger(name)
        dictConfig(conf)

    return logger
