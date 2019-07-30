#! /usr/bin/env python3
"""Client that fetches new emails."""
import email
import functools
import logging
import socket
import ssl
import time

from typing import Callable, Dict, List, NamedTuple, Optional

import pandas as pd
import schedule

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError, LoginError

from zippy.pipeline.model.rank_message import rank_message
from zippy.pipeline.model.update_dataset import online_training
from zippy.utils.config import get_config
from zippy.utils.log_handler import get_logger


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


class ProcessedMessage(NamedTuple):
    """Container to hold processed message."""

    msg: pd.DataFrame
    rank: float
    important: bool
    intent: bool


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


def get_server(
    config: dict,
    logger: logging.Logger,
    protocol=ssl.PROTOCOL_SSLv23,
    verify_cert: bool = False,
) -> IMAPClient:
    """Return server."""
    ssl_context = ssl.SSLContext(protocol)
    if not verify_cert:
        ssl_context.verify_flags = ssl.CERT_OPTIONAL
    else:
        ssl_context.verify_mode = ssl.CERT_REQUIRED

    try:
        server = IMAPClient(
            config["hostname"],
            port=config["imap_port"],
            ssl=config.get("ssl", True),
            ssl_context=ssl_context,
            timeout=config.get("timeout", 10),
        )
    except ssl.SSLError:
        logger.exception("Error due to ssl.")
        raise
    except socket.error:
        logger.exception("Could not connect to the mail server.")
        raise
    else:
        return server


def create_folder_if_not_exists(
    server: IMAPClient, folder: str, logger: logging.Logger
):
    """Create folder if it already exists."""
    try:
        server.create_folder(folder)
    except IMAPClientError:
        # most likely, it already exists
        logger.info("Looks like the folder %s already exists.", folder)


def shift_mail(server: IMAPClient, uid: int, destination: str, logger: logging.Logger):
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


def mark_processed(server: IMAPClient, uid: int, logger: logging.Logger):
    """Add flags to not check the emails again."""
    # imap: IMAP4_stream = server._imap
    # imap.uid("STORE", str(uid), "+FLAGS", f"({FLAG_TO_CHECK})")
    # `add_flags` returns new flags added, but if they are already there
    # it doesnot returns empty. So, confirm via `get_flags`.
    flag = b"processed"
    flags = server.get_flags(uid)
    logger.info("Result: %s, %s", flags, uid)
    if uid not in flags:
        logger.warn("Mail with uid: %s does not exist", uid)
        return
    if flag not in flags.get(uid):
        flags = server.add_flags(uid, flag)
        if uid not in flags:
            logger.warn(
                "Mail (uid: %s) could not added " "Weights might get updated twice", uid
            )
        else:
            logger.info("Flag added to %s", uid)


def process_mail(
    server: IMAPClient, uid: int, message_data: dict, logger: logging.Logger
) -> ProcessedMessage:
    """Process mail."""
    email_message = email.message_from_bytes(message_data[MESSAGE_FORMAT])
    msg = rank_message(email_message)
    processed_msg = ProcessedMessage(*msg)
    logger.info(
        "Rank: %s, Important: %s, Intent: %s, Subject: %s",
        processed_msg.rank,
        processed_msg.important,
        processed_msg.intent,
        email_message["subject"],
    )
    if processed_msg.important and not processed_msg.intent:
        shift_mail(
            server=server, uid=uid, destination=EmailFolders.IMPORTANT, logger=logger
        )
    elif processed_msg.important and processed_msg.intent:
        shift_mail(
            server=server, uid=uid, destination=EmailFolders.URGENT, logger=logger
        )

    mark_processed(server=server, uid=uid, logger=logger)

    return processed_msg


def process_mails(
    server: IMAPClient, uids: List[int], logger: logging.Logger
) -> Dict[int, ProcessedMessage]:
    """Retrieve all mails and process them, one by one."""
    processed_msgs: Dict[int, ProcessedMessage] = {}
    for uid, message_data in server.fetch(uids, MESSAGE_FORMAT).items():
        processed_msgs[uid] = process_mail(server, uid, message_data, logger)

    return processed_msgs


def retrieve_new_emails(
    server: IMAPClient, user: EmailAuthUser, logger: Optional[logging.Logger] = None
) -> List[int]:
    """Retrieve new unseen emails for the user."""
    logger = logger or get_logger(CLIENT)
    mails: List[int] = []
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
        raise
    except Exception as exc_info:  # pylint: disable=broad-except
        logger.exception("Unknown Exception occured. %s", str(exc_info))
        server.shutdown()
        raise
    else:
        server.select_folder(EmailFolders.INBOX, readonly=True)

        create_folder_if_not_exists(server, EmailFolders.IMPORTANT, logger)
        create_folder_if_not_exists(server, EmailFolders.URGENT, logger)

        search_key = b"UNSEEN UNKEYWORD " + FLAG_TO_CHECK

        logger.debug("Searching for unseen emails flagged '%s'", FLAG_TO_CHECK)
        mails = server.search(search_key)

    return mails


def online_train_all(processed_messages: Dict[int, ProcessedMessage]):
    """Update weights from processed messages."""
    for _, train_args in processed_messages.items():
        online_training(*train_args)


@with_logging
def main(
    config: dict,
    user: EmailAuthUser,
    server: Optional[IMAPClient] = None,
    logger: Optional[logging.Logger] = None,
):
    """Handle all updates for a specific users."""
    logger = logger or get_logger(CLIENT)
    server = server or get_server(config, logger=logger)
    with server:
        unprocessed_mails = retrieve_new_emails(server, user, logger)
        processed_messages = process_mails(server, unprocessed_mails, logger)
        online_train_all(processed_messages)


if __name__ == "__main__":
    CLIENT_CONFIG = get_config(CLIENT)
    for email_user in get_users(CLIENT_CONFIG):
        schedule.every(10).seconds.do(main, CLIENT_CONFIG, email_user)

    while True:
        schedule.run_pending()
        time.sleep(1)
