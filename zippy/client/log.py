"""Setup logger."""
import logging
import pathlib

from logging.config import dictConfig

import yaml


def get_logger():
    """Return logger."""
    env_file = pathlib.Path("../../.env.yml")
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
    handler = logging.FileHandler("../../output/logs/daemon.log")
    handler.setLevel(logging.DEBUG)

    # create a logging format
    formatter = logging.Formatter(
        "%(threadName)s %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    return logger
