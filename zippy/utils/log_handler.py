"""Custom Log Handler."""
import logging
import pathlib

from logging.config import dictConfig
from logging.handlers import RotatingFileHandler

from zippy.utils import config


class ZippyFileLogHandler(RotatingFileHandler):
    """Custom log handler that saves log to output dir even if called from any dir."""

    def __init__(self, filename, *args, **kwargs):
        log_dir = pathlib.Path(__file__).parents[2] / "output" / "logs"
        super().__init__(log_dir / filename, *args, **kwargs)


def get_logger(name: str):
    """Return logger if in config, else use basic console."""
    conf = config.get_config("logger")

    if conf:
        dictConfig(conf)
        logger = logging.getLogger(name)
    else:
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
    return logger
