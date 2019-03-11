"""Setup logger."""
import logging
import logging.handlers
import pathlib

from logging.config import dictConfig

import yaml

from zippy.utils.log_handler import ZippyFileLogHandler


def get_logger():
    """Return logger."""
    env_file = pathlib.Path(__file__).parents[2] / ".env.yml"

    logging.handlers.ZippyFileLogHandler = ZippyFileLogHandler

    if env_file.exists():
        config = yaml.safe_load(env_file.open())
        client_config = config.get("CLIENT")
        if client_config:
            log_config = client_config.get("logger")
            if log_config:
                dictConfig(log_config)
                return logging.getLogger("client_daemon")

    logger = logging.getLogger("client_daemon")

    logger.setLevel(logging.DEBUG)

    logger.info("Logger settings seems not to be set in ../../.env.yml .")
    handler = ZippyFileLogHandler("daemon.log")
    handler.setLevel(logging.DEBUG)

    # create a logging format
    formatter = logging.Formatter(
        "%(threadName)s %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    return logger