# pylint: disable=redefined-outer-name
"""Test for HyperParams class."""
import tempfile

from io import StringIO
from typing import IO

import pytest
import yaml

from zippy.utils.params import HyperParams


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
    hyper_params = HyperParams(file=yaml_config.name)
    assert hyper_params.batch_size == 100  # pylint: disable=maybe-no-member
    assert hyper_params.split_ratio == 0.7  # pylint: disable=maybe-no-member


def test_hyperparam_with_config(yaml_config: IO[str]) -> None:
    """Test that custom config works from yaml file."""
    hyper_params = HyperParams(file=yaml_config.name, config="fast")
    assert hyper_params.batch_size == 1000  # pylint: disable=maybe-no-member
    assert hyper_params.split_ratio == 0.6  # pylint: disable=maybe-no-member


def test_hyperparams_with_not_existing_config(yaml_config: IO[str]) -> None:
    """Test that AttributeError is raised on not existing config."""
    with pytest.raises(AttributeError) as exc_info:
        HyperParams(file=yaml_config.name, config="slow")
    assert (
        str(exc_info.value)
        == f"Config 'slow' could not be found in '{yaml_config.name}'."
    )


def test_hyperparams_dot_dict_accesses(yaml_config: IO[str]) -> None:
    """Test dot and [] accesses."""
    hyper_params = HyperParams(file=yaml_config.name, config="default")

    assert hyper_params.batch_size == 100

    hyper_params.lr = 1
    hyper_params["alpha"] = 0.19

    assert "lr" in hyper_params
    assert hyper_params.lr == 1

    assert "alpha" in hyper_params
    assert hyper_params["alpha"] == 0.19

    del hyper_params["lr"]
    assert "lr" not in hyper_params

    del hyper_params.alpha
    assert "alpha" not in hyper_params


def test_stream_open_hyperparams(yaml_config: IO[str]) -> None:
    """Test opening via stream."""
    with open(yaml_config.name) as stream:
        hyper_params = HyperParams(stream=stream, config="default")

        assert hyper_params.batch_size == 100
        assert not stream.closed


def test_not_passing_any_args_should_have_empty_data() -> None:
    """Test passing no args should have empty data."""
    hyper_params = HyperParams()
    assert not hyper_params


def test_json_as_hyperparams() -> None:
    """Test that the hyperparams work with json also."""
    data = """{
        "default":
            {
                "batch_size": 100,
                "split_ratio": 0.7
            }
        }"""
    hyper_params = HyperParams(stream=StringIO(data))
    assert hyper_params.batch_size == 100
    assert hyper_params.split_ratio == 0.7
