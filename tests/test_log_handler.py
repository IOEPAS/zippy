"""Test log handler."""
import pathlib

from logging.handlers import RotatingFileHandler

from zippy.utils.log_handler import ZippyFileLogHandler


def test_zippy_should_place_log_in_output_log_dir():
    """Log is always placed in output/logs directory."""
    handler = ZippyFileLogHandler("test.log")
    expected_log_path = (
        pathlib.Path(__file__).parents[1] / "output" / "logs" / "test.log"
    )
    assert handler.baseFilename == str(expected_log_path)


def test_is_a_rotating_log_handler():
    """Test that log is rotated to multiple files if it exceeds size."""
    handler = ZippyFileLogHandler("test.log")
    assert isinstance(handler, RotatingFileHandler)
