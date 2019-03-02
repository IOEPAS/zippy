"""Test for client daemon."""
import os
import pathlib
import signal
import tempfile
import time

from subprocess import PIPE, Popen

import pytest


@pytest.mark.integration
@pytest.mark.xfail
def test_that_daemon_runs():
    """Test that daemon is running."""
    pid_file = pathlib.Path(tempfile.tempdir() / "zippy_daemon.pid")
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

    # cleanup
    while True:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
        except OSError:
            break


@pytest.mark.integration
@pytest.mark.xfail
def test_that_daemon_cleans_up_when_killed():
    """Test that daemon cleans up when killed."""
    pid_file = pathlib.Path(tempfile.tempdir() / "zippy_daemon.pid")

    Popen("./src/client/daemon.py", shell=True).wait()

    timeout = time.time() + 5  # 5 sec

    while time.time() < timeout:
        if pid_file.exists():
            break
        time.sleep(0.1)

    pid = int(pid_file.read_text().strip())

    while True:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
        except OSError:
            break

    assert not pid_file.exists()

    stdout, _ = Popen(["ps", "-p", str(pid)], stdout=PIPE, stderr=PIPE).communicate()

    processes = [str(line).split(" ", 1) for line in str(stdout.strip().splitlines())]

    assert str(pid) not in processes
