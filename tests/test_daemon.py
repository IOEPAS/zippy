# pylint: disable=redefined-outer-name
"""Test for client daemon."""
import os
import pathlib
import signal
import tempfile
import time

from subprocess import Popen

import mock
import pytest
import yaml

from zippy.client import daemon


@pytest.fixture
def env_with_config():
    """Create an environment with ZIPPY_CONFIG appended."""
    config = {
        "CLIENT": {
            "hostname": "localhost.org",
            "users": [
                {"username": "test0@localhost.org", "password": "test0"},
                {"username": "test1@localhost.org", "password": "test1"},
            ],
        }
    }

    config_file = pathlib.Path(tempfile.gettempdir()) / "env_config.yml"

    yaml.safe_dump(config, open(config_file, "w"))

    new_env = os.environ.copy()
    new_env["ZIPPY_CONFIG_FILE"] = str(config_file.absolute().resolve())

    yield new_env

    config_file.unlink()


@pytest.fixture(autouse=True)
def run_daemon(request, env_with_config):
    """Run daemon every time tests on this file/module is run."""
    if "integration" not in request.keywords:
        yield
        return

    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    assert not pid_file.exists()

    Popen("./zippy/client/daemon.py", shell=True, env=env_with_config).wait()

    timeout = time.time() + 5  # 5 sec

    while time.time() < timeout:
        if pid_file.exists():
            break
        time.sleep(0.1)

    assert pid_file.exists()

    pid = int(pid_file.read_text().strip())
    assert pid

    yield

    # pid might have changed after restart, so read again
    if pid_file.exists():
        new_pid = int(pid_file.read_text().strip())
    else:
        # no harm on trying to kill twice. if there's no new pid,
        # use old one as new again.
        new_pid = pid

    # cleanup
    while True:
        try:
            os.kill(new_pid, signal.SIGTERM)
            time.sleep(0.1)
        except OSError:
            if pid_file.exists():
                pid_file.unlink()
            break

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
def test_that_daemon_stops_when_stop_is_called(env_with_config):
    """Test that daemon stops up stop is called."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    Popen("./zippy/client/daemon.py stop", shell=True, env=env_with_config).wait()

    assert not pid_file.exists()

    with pytest.raises(OSError):
        os.kill(pid, 0)


@pytest.mark.integration
def test_that_daemon_restarts_when_restart_is_called(env_with_config):
    """Test that daemon restarts if restart is called."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    Popen("./zippy/client/daemon.py restart", shell=True, env=env_with_config).wait()

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
def test_if_daemon_running_again_start_should_fail(env_with_config):
    """Test that daemon does not start when another instance is already running."""
    pid_file = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"
    pid = int(pid_file.read_text().strip())

    # should exit with 1 if already running
    child = Popen("./zippy/client/daemon.py start", shell=True, env=env_with_config)
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


@pytest.mark.unittest
def test_daemon_start():
    """Test that daemon works."""
    with mock.patch.object(daemon.Daemon, "_daemonize") as daemonizer:
        with mock.patch.object(daemon.sys, "exit") as mock_exit:
            with mock.patch.object(daemon.Daemon, "_save_pid") as pid_save:
                with mock.patch.object(daemon.Daemon, "_get_pid") as get_pid:
                    get_pid.return_value = None
                    daemon.Daemon().start()
                get_pid.assert_called_once()
            pid_save.assert_called_once()
        mock_exit.assert_not_called()
    daemonizer.assert_called_once()


@pytest.mark.unittest
def test_daemon_start_when_pid_already_exists():
    """Test that the program exits if pid already exists."""
    with mock.patch.object(daemon.Daemon, "_daemonize") as daemonizer:
        with mock.patch.object(daemon.Daemon, "_save_pid") as pid_save:
            with mock.patch.object(daemon.Daemon, "_get_pid") as get_pid:
                get_pid.return_value = 2
                with pytest.raises(SystemExit) as exc:
                    daemon.Daemon().start()
                assert exc.value.code == 1
            get_pid.assert_called_once()
        pid_save.assert_not_called()
    daemonizer.assert_not_called()


@pytest.mark.unittest
def test_daemon_stop_when_doesnot_exist():
    """Test daemon stop if daemon is not running already."""
    with mock.patch.object(daemon.Daemon, "_get_pid") as get_pid:
        with mock.patch.object(daemon.os, "kill") as nuke:
            get_pid.return_value = None
            assert daemon.Daemon().stop() is None
    nuke.assert_not_called()
    get_pid.assert_called_once()


@pytest.mark.unittest
def test_daemon_stop_when_pid_exists():
    """Test daemon stop if daemon is already running."""
    with mock.patch.object(daemon.Daemon, "_get_pid") as get_pid:
        with mock.patch.object(daemon.Daemon, "_remove_pidfile") as pid_remover:
            with mock.patch.object(daemon.os, "kill") as nuke:
                get_pid.return_value = 3
                nuke.side_effect = OSError
                assert daemon.Daemon().stop() is None
        pid_remover.assert_called_once()
    nuke.assert_called_once_with(3, signal.SIGTERM)
    get_pid.assert_called_once()
