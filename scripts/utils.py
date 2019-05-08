"""Utilities to make our work easier."""
import datetime
import shutil

from pathlib import Path

import yaml

from azure.storage.blob import BlockBlobService

# Reading the environment variables
STREAM = open(".env.yml", "r")
CONFIG = yaml.safe_load(STREAM)

BLOCK_BLOB_SERVICE = BlockBlobService(
    account_name=CONFIG["AZURE_STORAGE_NAME"], account_key=CONFIG["AZURE_STORAGE_KEY"]
)

CONTAINER_NAME = CONFIG["CONTAINER_NAME"]


def copy_example(topic: str):
    """Create a copy of the ``example.ipynb`` file."""
    date = datetime.date.today().strftime("%Y%m%d")
    username = CONFIG["USERNAME"]
    file_name = f"notebooks/{date}-{username}-{topic}.ipynb"
    if not Path(file_name).exists():
        shutil.copy("notebooks/example.ipynb", file_name)
        print(f"Created {file_name} successfully.")
    else:
        print(f"File {file_name} already exists. Try with another name.")


def push_blob(file_path):
    """Write file to Azure blob storage."""
    blob_name = file_path.split("/")
    blob_name = "_".join(blob_name)
    file_exists = BLOCK_BLOB_SERVICE.exists(CONTAINER_NAME, blob_name)
    if file_exists:
        print("File already exists in Azure storage. Please try with another name.")
    else:
        BLOCK_BLOB_SERVICE.create_blob_from_path(CONTAINER_NAME, blob_name, file_path)
        print("{0} written to container {1}.".format(blob_name, CONTAINER_NAME))


def pull_blob(file_path):
    """Read file from Azure blob storage."""
    blob_name = file_path.split("/")
    blob_name = "_".join(blob_name)
    file_path = Path(file_path)
    folder_path = file_path.parent

    if file_path.exists():
        print("File {0} already exists.".format(file_path))
        return
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)
        print("{0} did not exist. Created.".format(folder_path))

    print("Downloading {0} to {1} ...".format(blob_name, file_path))

    BLOCK_BLOB_SERVICE.get_blob_to_path(CONTAINER_NAME, blob_name, str(file_path))
    print("{0} downloaded to {1}.".format(blob_name, file_path))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "create_nb":
            copy_example(sys.argv[2])
        elif sys.argv[1] == "pull":
            pull_blob(sys.argv[2])
        elif sys.argv[1] == "push":
            push_blob(sys.argv[2])
