"""Hyperparameters and App params related functions."""
from typing import IO, Optional

import yaml


class HyperParams(dict):
    """HParams with parameters loading capability from yaml files.

    Parameters
    ----------
    file: str, optional
        Path to yaml file
    stream: io.TextIOWrapper, optional
        Use already opened stream
    config: str, optional
        Config to use

    Raises
    ------
    AttributeError
        If config does not exist with given name
    """

    def __init__(
        self,
        file: Optional[str] = None,
        stream: Optional[IO[str]] = None,
        config: Optional[str] = "default",
    ) -> None:
        super().__init__()

        if stream:
            doc = yaml.safe_load(stream.read())
        elif file:
            with open(file, "r") as stream_:
                doc = yaml.safe_load(stream_.read())
        else:
            ## empty initialization
            return

        params = doc.get(config)

        if not params:
            raise AttributeError(f"Config '{config}' could not be found in '{file}'.")

        self.update(params)

    def __getattr__(self, key):
        """Make attribute of params available via dot operator."""
        return super().__getitem__(key)

    def __setattr__(self, key, value):
        """Set attribute of params via dot operator."""
        super().__setitem__(key, value)

    def __delattr__(self, key):
        """Make attribute of params deletable via dot operator."""
        super().__delitem__(key)
