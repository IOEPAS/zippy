#! /usr/bin/env python3
"""Background running program that checks for new mails and downloads them."""
import atexit
import concurrent.futures
import os
import pathlib
import signal
import socket
import ssl
import sys
import tempfile
import time

import yaml

from imapclient import IMAPClient
from imapclient.exceptions import LoginError

if __package__:
    # sphinx imports this module, so need to use relative imports for the purpose
    from .log import get_logger
else:
    # running this as script doesnot work with relative imports as there is no parent
    # TODO: split these and put it somewhere else to remove this kind of checks
    from log import get_logger  # type: ignore  #pylint: disable=no-name-in-module


LOGGER = get_logger()


class Daemon:
    """Create a daemon: background running task that checks for new emails."""

    PID_FILE = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"

    def __init__(self, disable=False):
        self.disable_daemon = disable

    def _daemonize(self):
        """Fork and daemonize."""
        if self.disable_daemon:
            return

        LOGGER.debug("Daemonizing...")

        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write("fork #1 failed: {0}\n".format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork. why?
        # see: https://stackoverflow.com/q/881388
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write("fork #2 failed: {0}\n".format(err))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        stdin = open(os.devnull, "r")
        stdout = open(os.devnull, "a+")
        stderr = open(os.devnull, "a+")
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())

        LOGGER.debug("Daemonized successfully.")

        # write pid file

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        atexit.register(self._remove_pidfile)
        self._save_pid()

    def _remove_pidfile(self):
        LOGGER.info("Removing PID file...")
        self.PID_FILE.unlink()

    def start(self):
        """Start daemon."""
        pid = self._get_pid()
        if pid:
            sys.stderr.write(f"Another instance with pid: {pid} already running.\n")
            sys.exit(1)
        self._daemonize()
        self._save_pid()

        return self

    def __enter__(self):
        """Context manager that creates daemon."""
        self.start()
        return self

    def __exit__(self, *args):
        """Context manager that destroys daemon."""
        self.stop()
        sys.exit(0)

    def _get_pid(self):
        if self.PID_FILE.exists():
            pid = int(self.PID_FILE.read_text().strip())
            return pid
        return None

    def _save_pid(self):
        with self.PID_FILE.open("w") as pid_file:
            pid = os.getpid()
            pid_file.write(str(pid))
            pid_file.flush()

    def stop(self):
        """Kill the running daemon."""
        # Try killing the daemon process
        pid = self._get_pid()

        if not pid:
            sys.stderr.write(
                f"pid file {self.PID_FILE} does not exist. Daemon not running?\n"
            )
            return

        LOGGER.debug("Shutting down the daemon.")

        while True:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)
            except OSError:
                if self.PID_FILE.exists():
                    self.PID_FILE.unlink()
                    LOGGER.info("Removed PID file")
                break


def download_new_email(username, password, host, imap_port=993, timeout=3):
    """Check for new emails and download them.

    Parameters
    ----------
    username:
    password:
    host:
    imap_port:


    Raises
    ------
    ssl.SSLError
        Due to ssl verification
    socket.error
        Connection to server timed out. Server is offline or network is down
    LoginError:
        If credentials are incorrect


    .. todo:: Downloading emails when notified, as currently is only gets
        notifications.
    """
    # We are using ssl but let's not enforce it strictly
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.verify_flags = ssl.CERT_OPTIONAL

    LOGGER.debug(username)

    try:
        server = IMAPClient(
            host, port=imap_port, ssl=True, ssl_context=ssl_context, timeout=timeout
        )
    except socket.error:
        LOGGER.exception("Could not connect to the mail server.")
        return
    except ssl.SSLError:
        LOGGER.exception("Error due to ssl.")
        return

    try:
        server.login(username, password)
        server.select_folder("INBOX")
    except LoginError:
        LOGGER.exception("Credentials could not be verified for '%s'.", username)
        server.shutdown()
        return

    while True:
        # reconnect every 7 mins, as per recommendation to do so.
        timeout = time.time() + 7 * 60  # after 7 mins

        # Start IDLE mode
        try:
            server.idle()
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected exception occurred.")
            return
        else:
            LOGGER.info(
                "Connection is now in IDLE mode, send yourself an email or quit with ^c"
            )

        curr_time = time.time()
        while curr_time < timeout:
            try:
                # Wait for up to 30 seconds for an IDLE response
                responses = server.idle_check(timeout=30)
                # if server was up, response should have come as timeout is 30sec.
                # so, it's not required to check for socket.error here.
            # log the unexpected exception
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected error occurred.")
                return
            else:
                LOGGER.info(
                    "Server sent: %s for %s",
                    responses if responses else "nothing",
                    username,
                )
            time.sleep(10)

        try:
            server.idle_done()
        # nothing expected exception here. but let's log these if it occurs.
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected error occurred.")
            return
        else:
            LOGGER.info("\nIDLE mode done")
            time.sleep(10)


if __name__ == "__main__":
    STREAM = open("../../.env.yml", "r")
    CONFIG = yaml.safe_load(STREAM)
    CLIENT_CONFIG = CONFIG.get("CLIENT")
    if not CLIENT_CONFIG:
        print("Config not setup properly. Check env.example.yml for more info.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        Daemon().stop()
    else:
        if len(sys.argv) > 1 and sys.argv[1] == "restart":
            Daemon().stop()
            MESSAGE = "Daemon restarted."
            LOGGER.info(MESSAGE)
            print(MESSAGE)

        CREDENTIALS = CLIENT_CONFIG.get("users")

        with Daemon(disable=CLIENT_CONFIG.get("debug", False)) as d:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(CREDENTIALS)
            ) as executor:
                for credential in CREDENTIALS:
                    executor.submit(
                        download_new_email,
                        credential["username"],
                        credential["password"],
                        CLIENT_CONFIG["hostname"],
                        CLIENT_CONFIG.get("imap_port", 993),
                        CLIENT_CONFIG.get("timeout", 3),
                    )
                executor.shutdown(wait=True)
