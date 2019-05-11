"""Handle config management for client."""
import os
import pathlib

import yaml


def get_config(config):
    """Return config from config.file."""
    file = pathlib.Path(__file__).parents[2] / ".env.yml"
    if os.environ.get("ZIPPY_CONFIG_FILE"):
        file = pathlib.Path(os.environ["ZIPPY_CONFIG_FILE"])

    stream = file.open("r")
    env = yaml.safe_load(stream)
    conf = env.get(config)

    if conf is None:
        message = (
            f"{config} config missing. Please see 'env.example.yml' for example usage."
        )
        raise ValueError(message)
    return conf
