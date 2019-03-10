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

from imapclient import IMAPClient
from imapclient.exceptions import LoginError

from zippy.utils.config import get_config
from zippy.utils.log import get_logger

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
        if self.PID_FILE.exists():
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
        if self.disable_daemon:
            return

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
                self._remove_pidfile()
                break


def block_till_new_mail(server, timeout=60):
    """Return true if there's new mail, else checks for timeout."""
    failure = 0

    while time.time() < timeout:
        if failure >= 10:
            failure = 1

        try:
            # Wait for up to 30 seconds for an IDLE response
            responses = server.idle_check(timeout=30)
            # if server was up, response should have come as timeout is 30sec.
            # so, it's not required to check for socket.error here.
        # log the unexpected exception
        except socket.error:
            failure += 1
            LOGGER.info("Sleeping for %s second", failure * 10)
            time.sleep(failure * 10)
            continue
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected error occurred.")
            raise
        else:
            failure = 0
            if responses:
                return True
        time.sleep(10)

    try:
        server.idle_done()
    # nothing expected exception here. but let's log these if it occurs.
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Unexpected error occurred.")
        raise
    else:
        LOGGER.info("\nIDLE mode done")
        time.sleep(10)
        return False


def download_new_email(
    username, password, host, imap_port=993, timeout=3
):  # pylint:disable=too-many-branches,too-many-statements
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

    failure = 0

    while True:
        if failure > 10:
            failure = 1

        try:
            server = IMAPClient(
                host, port=imap_port, ssl=True, ssl_context=ssl_context, timeout=timeout
            )
        except socket.error:
            LOGGER.exception("Could not connect to the mail server.")
            failure += 1
            LOGGER.info("Sleeping for %s second", failure * 10)
            time.sleep(10 * failure)
            continue
        except ssl.SSLError:
            LOGGER.exception("Error due to ssl.")
            break
        else:
            failure = 0

        try:
            server.login(username, password)
            server.select_folder("INBOX")
        except LoginError:
            LOGGER.exception("Credentials could not be verified for '%s'.", username)
            server.shutdown()
            break
        except socket.error:
            LOGGER.exception("Could not connect to the mail server.")
            failure += 1
            time.sleep(10 * failure)
            continue
        else:
            failure = 0

        while True:
            # reconnect every 7 mins, as per recommendation to do so.
            timeout = int(time.time()) + 7 * 60  # after 7 mins

            try:
                server.idle()
            except socket.error:
                LOGGER.exception("Could not connect to the mail server.")
                break
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception occurred.")
                return
            else:
                failure = 0
                LOGGER.info(
                    "Connection is now in IDLE mode, send yourself an email or quit with ^c"
                )

            has_new_mail = block_till_new_mail(server, timeout=timeout)
            if has_new_mail:
                pass


if __name__ == "__main__":
    CLIENT_CONFIG = get_config("CLIENT")
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
