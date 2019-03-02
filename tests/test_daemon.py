"""Test for client daemon."""
import os
import pathlib
import signal
import tempfile
import time

from subprocess import Popen

import pytest


@pytest.fixture(autouse=True)
def run_daemon():
    """Run daemon every time tests on this file/module is run."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    assert not pid_file.exists()

    Popen("./src/client/daemon.py", shell=True).wait()

    timeout = time.time() + 5  # 5 sec

    while time.time() < timeout:
        if pid_file.exists():
            break
        time.sleep(0.1)

    assert pid_file.exists()

    pid = int(pid_file.read_text().strip())
    assert pid

    yield

    # cleanup
    while True:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
        except OSError:
            if pid_file.exists():
                pid_file.unlink()
            break


@pytest.mark.integration
@pytest.mark.xfail
def test_that_daemon_runs():
    """Test that daemon is running."""

    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    try:
        os.kill(pid, 0)
    except OSError:
        assert False, "daemon is currently not running."
    else:
        pass


@pytest.mark.integration
@pytest.mark.xfail
def test_that_daemon_cleans_up_when_killed():
    """Test that daemon cleans up when killed."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    while True:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
        except OSError:
            break

    assert not pid_file.exists()

    with pytest.raises(OSError):
        os.kill(pid, 0)


@pytest.mark.integration
@pytest.mark.xfail
def test_that_daemon_stops_when_stop_is_called():
    """Test that daemon stops up stop is called."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    Popen("./src/client/daemon.py stop", shell=True).wait()

    assert not pid_file.exists()

    with pytest.raises(OSError):
        os.kill(pid, 0)


@pytest.mark.integration
@pytest.mark.xfail
def test_that_daemon_restarts_when_restart_is_called():
    """Test that daemon restarts if restart is called."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    Popen("./src/client/daemon.py restart", shell=True).wait()

    # old process should have been stopped
    with pytest.raises(OSError):
        os.kill(pid, 0)

    assert pid_file.exists()
    new_pid = int(pid_file.read_text().strip())
    assert new_pid

    try:
        os.kill(new_pid, 0)
    except OSError:
        assert False, "daemon is currently not running."
    else:
        pass


@pytest.mark.integration
@pytest.mark.xfail
def test_if_daemon_running_again_start_should_fail():
    """Test that daemon does not start when another instance is already running."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    # should exit with 1 if already running
    child = Popen("./src/client/daemon.py start", shell=True)
    child.communicate()
    assert child.returncode == 1

    try:
        os.kill(pid, 0)
    except OSError:
        assert False, "daemon got killed running start again."
    else:
        pass

    assert int(pid_file.read_text().strip()) == pid

    # pid file should exist and content should not have been replaced
    assert pid_file.exists()
    new_pid = int(pid_file.read_text().strip())
    assert new_pid
