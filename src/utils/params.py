"""Hyperparameters and App params related functions."""
import yaml

from tensorflow.contrib.training import HParams  # pylint: disable=no-name-in-module


class HyperParams(HParams):
    """HParams with parameters loading capability from yaml files."""

    def parse_yaml(self, file: str, config: str = "default") -> "HyperParams":
        """
        Parse yaml file to use as hyperparameters.

        Parameters
        ----------
        file:
            Path to yaml file
        config:
            Config to use

        Returns
        -------
        HyperParams:
            hyperparameter instance

        Raises
        ------
        AttributeError
            If config doesnot exist with given name

        """
        with open(file) as stream:
            doc = yaml.load(stream)
            params = doc.get(config)
            if not params:
                raise AttributeError(
                    f"Config '{config}' could not be found in '{file}'."
                )

            for key, value in params.items():
                self.add_hparam(key, value)
        return self

    def to_yaml(self, config: str = "default") -> str:
        """
        Serialize hyperparameters to yaml.

        Parameters
        ----------
        config:
            Config to dump

        Returns
        -------
        str:
            yaml string

        Raises
        ------
        NotImplementedError

        """
        raise NotImplementedError("Serializing to yaml is not currently supported.")
