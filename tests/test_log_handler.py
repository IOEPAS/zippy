"""Test log handler."""
# pylint: disable=redefined-outer-name
import logging
import os
import pathlib
import tempfile

from logging.handlers import RotatingFileHandler

import pytest
import yaml

from zippy.utils.log_handler import ZippyFileLogHandler


@pytest.fixture()
def config_file():
    """Config file with logger set up."""
    config = {"logger": {"version": 1, "loggers": {"test": {"level": "DEBUG"}}}}
    tmp_config_file = pathlib.Path(tempfile.gettempdir()) / ".env.yml"
    yaml.safe_dump(config, open(tmp_config_file, "w"))

    yield tmp_config_file
    tmp_config_file.unlink()


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


def test_get_logger_positive(config_file):
    """Test get_logger happy path."""
    os.environ["ZIPPY_CONFIG_FILE"] = str(config_file.absolute().resolve())

    from zippy.utils.log_handler import get_logger

    logger = get_logger("test")
    assert logger.getEffectiveLevel() == logging.DEBUG
    assert logger.name == "test"


def test_get_logger_on_no_key_found(config_file):
    """Test get_logger if no module name exist in config."""
    os.environ["ZIPPY_CONFIG_FILE"] = str(config_file.absolute().resolve())

    from zippy.utils.log_handler import get_logger

    logger = get_logger("testA")
    assert logger.getEffectiveLevel() == logging.WARNING
    assert logger.name == "testA"


def test_get_logger_on_logger_set_on_config(config_env_file):
    """Test get_logger return logger when no config is set."""
    os.environ["ZIPPY_CONFIG_FILE"] = str(config_env_file.absolute().resolve())

    from zippy.utils.log_handler import get_logger

    logger = get_logger("testA")
    assert logger.getEffectiveLevel() == logging.DEBUG
    assert logger.name == "testA"
