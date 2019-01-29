"""Utilities to make our work easier."""
import os, datetime
import shutil
import yaml
from pathlib import Path
from azure.storage.blob import BlockBlobService

# Reading the environment variables
stream = open('.env.yml', 'r')
config = yaml.load(stream)

block_blob_service = BlockBlobService(account_name=config['AZURE_STORAGE_NAME'], account_key=config['AZURE_STORAGE_KEY'])

container_name = config['CONTAINER_NAME']

file_path = os.getcwd() + '/data/'

def copy_example(topic: str):
    """Creates a copy of the ``example.ipynb`` file."""

    date = datetime.date.today().strftime("%Y%m%d")
    username = config["USERNAME"]
    file_name = f"notebooks/{date}-{username}-{topic}.ipynb"
    if not Path(file_name).exists():
        shutil.copy("notebooks/example.ipynb", file_name)
        print(f"Created {file_name} successfully.")
    else:
        print(f"File {file_name} already exists. Try with another name.")

def push_blob(new_blob_name):
    """ Write file to Azure blob storage. """
    block_blob_service.create_blob_from_path(container_name, new_blob_name, file_path + new_blob_name)
    print('{0} written to container {1}.'.format(new_blob_name, container_name))

def pull_blob(blob_name):
    """ Read file from Azure blob storage. """
    block_blob_service.get_blob_to_path(container_name, blob_name, file_path + blob_name)
    print('{0} downloaded to {1}.'.format(blob_name, file_path))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "create_nb":
            copy_example(sys.argv[2])
        if sys.argv[1] == "pull":
            pull_blob(sys.argv[2])
        if sys.argv[1] == "push":
            push_blob(sys.argv[2])