"""Configure tests before running."""
import os
import pathlib
import shutil
import tempfile

import pytest


@pytest.fixture(autouse=True)
def setup_file():
    """Set pytest before running."""
    tmp_config_file = pathlib.Path(tempfile.gettempdir()) / "env_config.yml"
    example_config_file = pathlib.Path(__file__).parents[2] / "env.example.yml"

    # copy file
    shutil.copy(example_config_file, tmp_config_file)

    # used to read config from `get_config`
    os.environ["ZIPPY_CONFIG_FILE"] = str(tmp_config_file.absolute().resolve())

    yield

    os.environ.unsetenv("ZIPPY_CONFIG_FILE")
    tmp_config_file.unlink()
