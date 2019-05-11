"""Setup and set fixtures for tests."""
import pathlib
import tempfile

import pytest
import yaml


@pytest.fixture()
def config_env_file():
    """Config file to test for."""
    config = {
        "client": {
            "hostname": "localhost.org",
            "users": [
                {"username": "test1@localhost.org", "password": "test1"},
                {"username": "test2@localhost.org", "password": "test2"},
            ],
        }
    }

    tmp_config_file = pathlib.Path(tempfile.gettempdir()) / ".env.yml"
    yaml.safe_dump(config, open(tmp_config_file, "w"))

    yield tmp_config_file
    tmp_config_file.unlink()
