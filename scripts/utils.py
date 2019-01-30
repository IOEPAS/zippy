"""Utilities to make our work easier."""
import datetime
import shutil

from pathlib import Path

import yaml

from azure.storage.blob import BlockBlobService

# Reading the environment variables
STREAM = open(".env.yml", "r")
CONFIG = yaml.load(STREAM)

BLOCK_BLOB_SERVICE = BlockBlobService(
    account_name=CONFIG["AZURE_STORAGE_NAME"], account_key=CONFIG["AZURE_STORAGE_KEY"]
)

CONTAINER_NAME = CONFIG["CONTAINER_NAME"]


def copy_example(topic: str):
    """Creates a copy of the ``example.ipynb`` file."""

    date = datetime.date.today().strftime("%Y%m%d")
    username = CONFIG["USERNAME"]
    file_name = f"notebooks/{date}-{username}-{topic}.ipynb"
    if not Path(file_name).exists():
        shutil.copy("notebooks/example.ipynb", file_name)
        print(f"Created {file_name} successfully.")
    else:
        print(f"File {file_name} already exists. Try with another name.")


def push_blob(file_path):
    """ Write file to Azure blob storage. """
    blob_name = file_path.split("/")
    blob_name = "-".join(blob_name)
    file_exists = BLOCK_BLOB_SERVICE.exists(CONTAINER_NAME, blob_name)
    if file_exists:
        print("File already exists in Azure storage. Please try with another name.")
    else:
        BLOCK_BLOB_SERVICE.create_blob_from_path(CONTAINER_NAME, blob_name, file_path)
        print("{0} written to container {1}.".format(blob_name, CONTAINER_NAME))


def pull_blob(file_path):
    """ Read file from Azure blob storage. """
    blob_name = file_path.split("/")
    blob_name = "-".join(blob_name)
    if not Path(file_path).exists():
        BLOCK_BLOB_SERVICE.get_blob_to_path(CONTAINER_NAME, blob_name, file_path)
        print("{0} downloaded to {1}.".format(blob_name, file_path))
    else:
        print(f"File {file_path} already exists.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "create_nb":
            copy_example(sys.argv[2])
        elif sys.argv[1] == "pull":
            pull_blob(sys.argv[2])
        elif sys.argv[1] == "push":
            push_blob(sys.argv[2])
