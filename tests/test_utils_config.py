"""Test config."""
# pylint: disable=redefined-outer-name
import os

import pytest


def test_get_config(config_env_file):
    """Get config happy path."""
    os.environ["ZIPPY_CONFIG_FILE"] = str(config_env_file.absolute().resolve())

    from zippy.utils.config import get_config

    expected = {
        "hostname": "localhost.org",
        "users": [
            {"username": "test1@localhost.org", "password": "test1"},
            {"username": "test2@localhost.org", "password": "test2"},
        ],
    }
    assert get_config("client") == expected


def test_get_config_negative(config_env_file):
    """Test get_config error."""
    os.environ["ZIPPY_CONFIG_FILE"] = str(config_env_file.absolute().resolve())

    from zippy.utils.config import get_config

    with pytest.raises(KeyError) as exc_info:
        get_config("random_key_yml")
    assert (
        str(exc_info.value)
        == "\"random_key_yml config missing. Please see 'env.example.yml' for example usage.\""
    )
