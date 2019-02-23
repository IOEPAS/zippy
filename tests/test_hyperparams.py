# pylint: disable=redefined-outer-name
"""Test for HyperParams class."""
import tempfile

from typing import IO

import pytest
import yaml

from src.utils.params import HyperParams


@pytest.fixture
def yaml_config() -> IO[str]:
    """Generate a yaml config file for test."""
    file: IO[str] = tempfile.NamedTemporaryFile(mode="w")
    data = {
        "default": {"batch_size": 100, "split_ratio": 0.7},
        "fast": {"batch_size": 1000, "split_ratio": 0.6},
    }
    source = yaml.safe_dump(data)
    file.write(source)
    file.seek(0)
    return file


def test_hyperparam_default(yaml_config: IO[str]) -> None:
    """Test that 'default' config is used on default."""
    hyper_params = HyperParams().parse_yaml(file=yaml_config.name)
    assert hyper_params.batch_size == 100  # pylint: disable=maybe-no-member
    assert hyper_params.split_ratio == 0.7  # pylint: disable=maybe-no-member


def test_hyperparam_with_config(yaml_config: IO[str]) -> None:
    """Test that custom config works from yaml file."""
    hyper_params = HyperParams().parse_yaml(file=yaml_config.name, config="fast")
    assert hyper_params.batch_size == 1000  # pylint: disable=maybe-no-member
    assert hyper_params.split_ratio == 0.6  # pylint: disable=maybe-no-member


def test_hyperparams_with_not_existing_config(yaml_config: IO[str]) -> None:
    """Test that AttributeError is raised on not existing config."""
    with pytest.raises(AttributeError) as exc_info:
        HyperParams().parse_yaml(file=yaml_config.name, config="slow")
    assert (
        str(exc_info.value)
        == f"Config 'slow' could not be found in '{yaml_config.name}'."
    )
