"""Tests for generating json."""
# pylint: disable=redefined-outer-name
import json
import tempfile

from io import BytesIO

import pytest

from zippy.utils.json_generator import write_json_output


@pytest.fixture
def output_stream():
    """Output stream for bytesio."""
    with BytesIO() as stream:
        yield stream


@pytest.fixture
def log_file():
    """Create a log file with 2 entries."""
    file = tempfile.NamedTemporaryFile(mode="w")
    file.write(
        """{"message": null, \
        "rank": 21.867468569824258,\
        "important": "False",\
        "intent": "False",\
        "subject": "hello world",\
        "uid": 27,\
        "from": "test0@localhost.org",\
        "to": "test1@localhost.org",\
        "threshold": 411.9452434660541}
        {"message": null,\
        "rank": 21.867468569824258,\
        "important": "False",\
        "intent": "False",\
        "subject": "hello world",\
        "uid": 27,\
        "from": "test1@localhost.org",\
        "to": "test0@localhost.org",\
        "threshold": 411.9452434660541}"""
    )
    file.seek(0)
    return file


@pytest.fixture
def single_log_file():
    """Create a log file with 1 entry."""
    file = tempfile.NamedTemporaryFile(mode="w")
    file.write(
        """{"message": null, \
        "rank": 21.867468569824258,\
        "important": "False",\
        "intent": "False",\
        "subject": "hello world",\
        "uid": 27,\
        "from": "test0@localhost.org",\
        "to": "test1@localhost.org",\
        "threshold": 411.9452434660541}"""
    )
    file.seek(0)
    return file


@pytest.fixture
def log_on_same_line():
    """Create a log file with multiple entries on same line."""
    file = tempfile.NamedTemporaryFile(mode="w")
    file.write('{"message": 1}{"message": 2}{"message": 3}')
    file.seek(0)
    return file


@pytest.fixture
def log_comma_separation_same_line():
    """Create a log file with multiple entries on same line, comma separated."""
    file = tempfile.NamedTemporaryFile(mode="w")
    file.write('{"message": 1},{"message": 2},{"message": 3}')
    file.seek(0)
    return file


@pytest.fixture
def empty_log_file():
    """Create a log file without any entries."""
    file = tempfile.NamedTemporaryFile(mode="w")
    file.write("")
    file.seek(0)
    return file


def test_logfile(log_file, output_stream):
    """Test log file happy path with 2 logs."""
    with open(log_file.name, "rb") as file:
        write_json_output(file, output_stream)

    try:
        json_log = json.loads(output_stream.getvalue())
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log) == 2
        assert json_log[0]["from"] == "test0@localhost.org"
        assert json_log[1]["from"] == "test1@localhost.org"


def test_empty_logfile(empty_log_file, output_stream):
    """Test empty logs."""
    with open(empty_log_file.name, "rb") as file:
        write_json_output(file, output_stream)

    try:
        json_log = json.loads(output_stream.getvalue())
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert not json_log


def test_single_logfile(single_log_file, output_stream):
    """Test with single log."""
    with open(single_log_file.name, "rb") as file:
        write_json_output(file, output_stream)

    try:
        json_log = json.loads(output_stream.getvalue())
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log) == 1
        assert json_log[0]["from"] == "test0@localhost.org"


def test_logfile_log_entries_on_same_line(log_on_same_line, output_stream):
    """Test with single log."""
    with open(log_on_same_line.name, "rb") as file:
        write_json_output(file, output_stream)

    try:
        json_log = json.loads(output_stream.getvalue())
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log) == 3
        assert json_log[0]["message"] == 1
        assert json_log[1]["message"] == 2
        assert json_log[2]["message"] == 3


def test_logfile_log_entries_on_same_line_with_comma_separation(
    log_comma_separation_same_line, output_stream
):
    """Test with single log."""
    with open(log_comma_separation_same_line.name, "rb") as file:
        write_json_output(file, output_stream)

    try:
        json_log = json.loads(output_stream.getvalue())
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log) == 3
        assert json_log[0]["message"] == 1
        assert json_log[1]["message"] == 2
        assert json_log[2]["message"] == 3
