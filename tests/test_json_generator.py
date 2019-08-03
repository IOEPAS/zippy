"""Tests for generating json."""
# pylint: disable=redefined-outer-name
import json
import tempfile

import pytest

from zippy.utils.json_generator import wrap_json_output


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


def test_logfile(log_file):
    """Test log file happy path with 2 logs."""
    output = ""
    with open(log_file.name) as file:
        for line in wrap_json_output(file):
            output += line

    try:
        json_log = json.loads(output)
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log["logs"]) == 2
        assert json_log["logs"][0]["from"] == "test0@localhost.org"
        assert json_log["logs"][1]["from"] == "test1@localhost.org"


def test_empty_logfile(empty_log_file):
    """Test empty logs."""
    output = ""
    with open(empty_log_file.name) as file:
        for line in wrap_json_output(file):
            output += line

    try:
        json_log = json.loads(output)
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert not json_log["logs"]


def test_single_logfile(single_log_file):
    """Test with single log."""
    output = ""
    with open(single_log_file.name) as file:
        for line in wrap_json_output(file):
            output += line

    try:
        json_log = json.loads(output)
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log["logs"]) == 1
        assert json_log["logs"][0]["from"] == "test0@localhost.org"


def test_logfile_log_entries_on_same_line(log_on_same_line):
    """Test with single log."""
    output = ""
    with open(log_on_same_line.name) as file:
        for line in wrap_json_output(file):
            output += line

    try:
        json_log = json.loads(output)
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log["logs"]) == 3
        assert json_log["logs"][0]["message"] == 1
        assert json_log["logs"][1]["message"] == 2
        assert json_log["logs"][2]["message"] == 3


def test_logfile_log_entries_on_same_line_with_comma_separation(
    log_comma_separation_same_line
):
    """Test with single log."""
    output = ""
    with open(log_comma_separation_same_line.name) as file:
        for line in wrap_json_output(file):
            output += line

    try:
        json_log = json.loads(output)
    except ValueError:
        assert False, "Invalid json generated."
    else:
        assert len(json_log["logs"]) == 3
        assert json_log["logs"][0]["message"] == 1
        assert json_log["logs"][1]["message"] == 2
        assert json_log["logs"][2]["message"] == 3
