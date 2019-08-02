#! /usr/bin/env python3
"""Client that update log to json file."""
import pathlib
import time

from os import path

PATH_TO_LOG_FILE = (
    pathlib.Path(__file__).parents[2] / "output" / "logs" / "display" / "output.log"
)
PATH_TO_LOG_JSON = (
    pathlib.Path(__file__).parents[2] / "output" / "logs" / "display" / "output.json"
)


def log_to_json():
    """Change log file to json."""
    json_structure = '{\n        "logs":[ '
    ending = "    ]\n    }"
    with open(PATH_TO_LOG_FILE) as file_open:
        for line in file_open:
            line = line.replace("}{", "},{")
            json_structure += line + ","
    json_structure = json_structure[:-1]
    json_structure += ending
    with open(PATH_TO_LOG_JSON, "w") as file_open:
        file_open.write(json_structure)
    print("JSON File updated")
    return json_structure


LAST_MODIFIED = path.getmtime(PATH_TO_LOG_FILE)
log_to_json()
while True:
    time.sleep(1)
    LAST_UPDATED = path.getmtime(PATH_TO_LOG_FILE)
    if LAST_UPDATED != LAST_MODIFIED:
        LAST_MODIFIED = LAST_UPDATED
        log_to_json()
