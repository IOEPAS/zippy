"""Utilities to make our work easier."""
import datetime
import shutil

from pathlib import Path

import yaml


def copy_example(topic: str):
    """Creates a copy of the ``example.ipynb`` file."""

    date = datetime.date.today().strftime("%Y%m%d")
    with open(".env.yml") as env_file:
        config = yaml.load(env_file)
        username = config["USERNAME"]
        file_name = f"notebooks/{date}-{username}-{topic}.ipynb"
        if not Path(file_name).exists():
            shutil.copy("notebooks/example.ipynb", file_name)
            print(f"Created {file_name} successfully.")
        else:
            print(f"File {file_name} already exists. Try with another name.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "create_nb":
            copy_example(sys.argv[2])
