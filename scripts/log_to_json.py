#! /usr/bin/env python3
"""Client that update log to json file."""
import pathlib
import time

from datetime import datetime

from watchdog.events import FileCreatedEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from zippy.utils.json_generator import wrap_json_output


class JSONLogHandler(PatternMatchingEventHandler):
    """Convert json-like logs to json when the log file changes."""

    def __init__(self):
        super().__init__(
            patterns=["*.log"], ignore_directories=True, case_sensitive=True
        )

    def on_modified(self, event):
        """Change log file to json."""
        log_input = event.src_path
        log_output = pathlib.Path(log_input).with_suffix(".json")

        with open(log_input) as input_file:
            with open(log_output, "w") as output_file:
                output_file.write("".join(wrap_json_output(input_file)))

        print(
            "JSON File updated on {curr_time}".format(curr_time=datetime.now().time())
        )

    on_created = on_modified


if __name__ == "__main__":
    PATH_TO_LOG_FOLDER = (
        pathlib.Path(__file__).parents[1] / "output" / "logs" / "display"
    )
    PATH_TO_LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    (PATH_TO_LOG_FOLDER / "output.log").touch()

    EVENT_HANDLER = JSONLogHandler()
    observer = Observer()  # pylint:disable=invalid-name

    observer.schedule(
        EVENT_HANDLER, path=str(PATH_TO_LOG_FOLDER.absolute()), recursive=False
    )
    observer.start()

    print("Monitoring log changes...")

    # regenerate all log on startup
    EVENT_HANDLER.on_created(
        FileCreatedEvent(src_path=str(PATH_TO_LOG_FOLDER / "output.log"))
    )

    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
