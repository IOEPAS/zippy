"""Custom Log Handler."""
import pathlib

from logging.handlers import RotatingFileHandler


class ZippyFileLogHandler(RotatingFileHandler):
    """Custom log handler that saves log to output dir even if called from any dir."""

    def __init__(self, filename, *args, **kwargs):
        log_dir = pathlib.Path(__file__).parents[2] / "output" / "logs"
        super().__init__(log_dir / filename, *args, **kwargs)
