#! /usr/bin/env python3
"""Background running program that checks for new mails and downloads them."""
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


class Daemon:
    """Create a daemon: background running task that checks for new emails."""

    PID_FILE = pathlib.Path(tempfile.gettempdir()) / "zippy_daemon.pid"

    def __init__(self, disable=False):
        self.disable_daemon = disable

    def _daemonize(self):
        """Fork and daemonize."""
        if self.disable_daemon:
            return

        pid = os.fork()

        if pid > 0:
            sys.exit(0)

    def start(self):
        """Start daemon."""
        if self.PID_FILE.exists():
            pid = self._get_pid()
            print(f"Another instance is already running with pid: {pid}")
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
        pid = self.stop()
        sys.exit(0 if pid else 1)

    def _get_pid(self):
        if self.PID_FILE.exists():
            pid = int(self.PID_FILE.read_text().strip())
            return pid
        return 0

    def _save_pid(self):
        with self.PID_FILE.open("w") as pid_file:
            pid = os.getpid()
            pid_file.write(str(pid))
            pid_file.flush()

    def stop(self):
        """Stop daemon."""
        pid = self._get_pid()
        if pid:
            self.PID_FILE.unlink()
            os.kill(pid, signal.SIGTERM)
            return pid
        return 0


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
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.verify_flags = ssl.CERT_NONE

    print(username)

    try:
        server = IMAPClient(
            host, port=imap_port, ssl=True, ssl_context=ssl_context, timeout=timeout
        )
    except socket.error:
        print("Could not connect to the mail server.")
        raise
    except ssl.SSLError:
        print("Error due to ssl.")
        raise

    try:
        server.login(username, password)
    except LoginError:
        print(f"Credentials could not be verified for '{username}'.")
        server.shutdown()
        raise

    server.select_folder("INBOX")

    while True:
        timeout = time.time() + 7 * 60  # after 7 mins

        # Start IDLE mode
        server.idle()
        print("Connection is now in IDLE mode, send yourself an email or quit with ^c")

        curr_time = time.time()
        while curr_time < timeout:
            # Wait for up to 30 seconds for an IDLE response
            responses = server.idle_check(timeout=30)
            print(
                "Server sent:",
                responses if responses else "nothing",
                f" for {username}",
            )

        server.idle_done()
        print("\nIDLE mode done")
        time.sleep(10)


if __name__ == "__main__":
    STREAM = open("../../.env.yml", "r")
    CONFIG = yaml.safe_load(STREAM)
    CLIENT_CONFIG = CONFIG.get("CLIENT")
    if not CLIENT_CONFIG:
        print("Problem with config.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        PID = Daemon().stop()
        if PID == 0:
            print("No other instance seems to be running.")
        sys.exit(0 if PID else 1)
    else:
        if len(sys.argv) > 1 and sys.argv[1] == "restart":
            Daemon().stop()

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
