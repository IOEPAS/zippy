#! /usr/bin/env python3
"""Client that fetches new emails."""
import email
import functools
import logging
import socket
import ssl
import time

from typing import Callable, List, NamedTuple, Optional

import schedule

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError, LoginError

from zippy.pipeline.model.rank_message import rank_message
from zippy.pipeline.model.update_dataset import online_training
from zippy.utils.config import get_config
from zippy.utils.log_handler import get_logger

SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
SSL_CONTEXT.verify_flags = ssl.CERT_OPTIONAL


class EmailAuthUser(NamedTuple):
    """Data class for email user."""

    email_address: str
    password: str
    name: Optional[str] = None

    def __repr__(self) -> str:
        """Return string representation for debugging purposes."""
        if self.name:
            return f"({self.name}, {self.email_address})"
        return self.email_address


class EmailFolders:
    """Constants for email folder."""

    IMPORTANT: str = "Important"
    URGENT: str = "Urgent"
    INBOX: str = "INBOX"


CLIENT: str = "client"
USERS: str = "users"
FLAG_TO_CHECK: bytes = b"processed"
MESSAGE_FORMAT: bytes = b"RFC822"


def get_users(client_config) -> List[EmailAuthUser]:
    """Create users from list."""
    users_list = client_config.get(USERS)
    if users_list is None:
        raise KeyError(f"Missing '{USERS}' config inside '{CLIENT}'")
    return [
        EmailAuthUser(user["username"], user["password"], user.get("name"))
        for user in users_list
    ]


def with_logging(
    func: Optional[Callable] = None, *, logger: Optional[logging.Logger] = None
) -> Callable:  # noqa: D202
    """Log when ever job is started and completed."""

    def decorator_logger(func) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or get_logger(CLIENT)
            log.info("LOG: Running job %s", func.__name__)
            result = func(*args, **kwargs)
            log.info("LOG: Job '%s' completed", func.__name__)
            return result

        return wrapper

    if func:
        return decorator_logger(func)
    return decorator_logger


def inject_server(
    func: Optional[Callable] = None, *, ssl_context: ssl.SSLContext
) -> Callable:  # noqa: D202
    """Create server connection each time."""

    def decorator_server_inject(func) -> Callable:
        @functools.wraps(func)
        def wrapper_server_inject(*args, **kwargs):
            config = get_config(CLIENT)
            logger = get_logger(CLIENT)
            try:
                server = IMAPClient(
                    config["hostname"],
                    port=config["imap_port"],
                    ssl=config.get("ssl", True),
                    ssl_context=ssl_context,
                    timeout=config.get("timeout", 10),
                )
            except socket.error:
                logger.exception("Could not connect to the mail server.")
            except ssl.SSLError:
                logger.exception("Error due to ssl.")
                raise
            else:
                logger.debug("Mail server created.")
                return func(server, *args, **kwargs)

        return wrapper_server_inject

    if func is None:
        return decorator_server_inject

    return decorator_server_inject(func)


@with_logging
@inject_server(ssl_context=SSL_CONTEXT)
def retrieve_new_emails(
    server: IMAPClient, user: EmailAuthUser, logger: Optional[logging.Logger] = None
) -> None:
    """Retrieve new emails (user api)."""
    _retrieve_new_emails(server, user, logger)


def create_folder_if_not_exists(
    server: IMAPClient, folder: str, logger: logging.Logger
):
    """Create folder if it already exists."""
    try:
        server.create_folder(folder)
    except IMAPClientError:
        # most likely, it already exists
        logger.info("Looks like the folder %s already exists.", folder)


def shift_mail(server: IMAPClient, uid: str, destination: str, logger: logging.Logger):
    """Shift mail with given uid to given destination folder."""
    try:
        server.move(uid, destination)
    except IMAPClientError as exc_info:
        # most likely the folder doesnot exists
        logger.exception(
            "Failed email (uid: %s) to move to %s folder: %s",
            uid,
            destination,
            str(exc_info),
        )
    else:
        logger.info("Email (uid: %s) moved to %s folder.", uid, destination)


def mark_processed(server: IMAPClient, uid: str, logger: logging.Logger):
    """Add flags to not check the emails again."""
    server.add_flags(uid, FLAG_TO_CHECK)
    # `add_flags` returns new flags added, but if they are already there
    # it doesnot returns empty. So, confirm via `get_flags`.
    flags = server.get_flags(uid)
    logger.info("Result: %s, %s", flags, uid)
    if uid not in flags:
        logger.warn("Mail with uid: %s does not exist", uid)
        return
    if FLAG_TO_CHECK not in flags.get(uid):
        logger.warn(
            "Mail (uid: %s) could not added " "Weights might get updated twice", uid
        )
        return

    logger.info("Flag added to %s", uid)


def process_mail(
    server: IMAPClient, uid: str, message_data: dict, logger: logging.Logger
):
    """Process mail."""
    email_message = email.message_from_bytes(message_data[MESSAGE_FORMAT])
    msg, rank, priority, intent = rank_message(email_message)
    logger.info(
        "Rank: %s, Priority: %s, Urgent: %s, Subject: %s",
        rank,
        priority,
        intent,
        email_message["subject"],
    )
    if priority and not intent:
        shift_mail(
            server=server, uid=uid, destination=EmailFolders.IMPORTANT, logger=logger
        )
    elif priority and intent:
        shift_mail(
            server=server, uid=uid, destination=EmailFolders.URGENT, logger=logger
        )
    else:
        mark_processed(server=server, uid=uid, logger=logger)

    # update weights afterwards
    online_training(msg, rank, priority, intent)


def process_mails(server: IMAPClient, uids: List[str], logger: logging.Logger):
    """Retrieve all mails and process them, one by one."""
    for uid, message_data in server.fetch(uids, MESSAGE_FORMAT).items():
        process_mail(server, uid, message_data, logger)


def _retrieve_new_emails(
    server: IMAPClient, user: EmailAuthUser, logger: Optional[logging.Logger] = None
) -> None:
    """Retrieve new unseen emails for the user."""
    logger = logger or get_logger(CLIENT)
    with server:
        try:
            server.login(user.email_address, user.password)
            logger.info("Logged in successful for %s", user)
        except LoginError:
            logger.exception(
                "Credentials could not be verified for '%s'.", user.email_address
            )
            server.shutdown()
            raise
        except socket.error:
            logger.exception("Could not connect to the mail server.")
            server.shutdown()
        else:
            server.select_folder(EmailFolders.INBOX, readonly=True)

            create_folder_if_not_exists(server, EmailFolders.IMPORTANT, logger)
            create_folder_if_not_exists(server, EmailFolders.URGENT, logger)

            search_key = b"UNSEEN UNKEYWORD " + FLAG_TO_CHECK

            logger.debug("Searching for unseen emails flagged '%s'", FLAG_TO_CHECK)
            unprocessed_messages: list = server.search(search_key)

            process_mails(server, unprocessed_messages, logger)


if __name__ == "__main__":
    for email_user in get_users(get_config(CLIENT)):
        schedule.every(10).seconds.do(
            retrieve_new_emails, email_user, get_logger(CLIENT)
        )

    while True:
        schedule.run_pending()
        time.sleep(1)
