import email
import imaplib
import os
import smtplib
import socket
import ssl
import time

from typing import Callable, List
from unittest import mock

import pytest

from imapclient import IMAPClient
from imapclient.exceptions import LoginError

from zippy.client.main import (
    FLAG_TO_CHECK,
    SEEN_FLAG,
    EmailAuthUser,
    EmailFolders,
    ProcessedMessage,
    create_folder_if_not_exists,
    get_client,
    mark_processed,
    process_mails,
    retrieve_new_emails,
    shift_mail,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("TEST_ON_DOVECOT") is None, reason="Can be run only with dovecot"
)


@pytest.fixture
def logger():
    import logging

    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    return logger


@pytest.fixture
def config():
    c = {
        "imap_port": 2143,
        "ssl": False,
        "hostname": "localhost",
        "smtp_port": 2025,
        "dovecot": False,
        "timeout": 10,
    }
    if os.environ.get("TEST_ON_DOVECOT"):
        c["imap_port"] = 1993
        c["ssl"] = True
        c["smtp_port"] = 1025
        c["dovecot"] = True
    yield c


@pytest.fixture
def imap_client(config: dict, logger):
    client = get_client(config, logger)
    yield client
    try:
        client.shutdown()
    except OSError:
        # must have already shutdown
        pass


@pytest.fixture(autouse=True)
def create_required_folders(logged_in_client: IMAPClient, logger):
    create_folder_if_not_exists(logged_in_client, EmailFolders.IMPORTANT, logger)
    create_folder_if_not_exists(logged_in_client, EmailFolders.URGENT, logger)


@pytest.fixture
def random_mail(logged_in_client: IMAPClient, config):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.verify_flags = ssl.CERT_OPTIONAL

    # send message
    server: smtplib.SMTP = smtplib.SMTP(config["hostname"], config["smtp_port"])
    if config["ssl"]:
        server.starttls(context=ssl_context)

    next_uid = logged_in_client.select_folder("INBOX", readonly=True)[b"UIDNEXT"]
    server.login("test0@localhost.org", "test0")
    message = """\\
    Subject: Hi there

    This message is sent from Python."""
    server.sendmail("test0@localhost.org", "test1@localhost.org", message)

    wait_till_mail_appears(logged_in_client, uid=next_uid)

    yield next_uid

    logged_in_client.select_folder(EmailFolders.INBOX)
    logged_in_client.delete_messages(next_uid)
    logged_in_client.expunge()


@pytest.fixture
def logged_in_client(config, logger):
    client = get_client(config, logger)
    client.login("test1@localhost.org", "test1")
    yield client
    try:
        client.logout()
    except imaplib.IMAP4.error:
        # must have already logged out
        pass
    try:
        client.shutdown()
    except OSError:
        # already shutdown
        pass


@pytest.fixture
def flagged_random_mail(logged_in_client: IMAPClient, random_mail):
    logged_in_client.select_folder(EmailFolders.INBOX)
    logged_in_client.add_flags(random_mail, FLAG_TO_CHECK)
    assert FLAG_TO_CHECK in logged_in_client.get_flags(random_mail).get(random_mail)

    # no need to cleanup, as the message will get deleted anyway
    return random_mail


@pytest.fixture
def random_folder(logged_in_client: IMAPClient):
    folder = "random-122122121"
    if not logged_in_client.folder_exists(folder):
        logged_in_client.create_folder(folder)

    yield folder

    if logged_in_client.folder_exists(folder):
        logged_in_client.delete_folder(folder)

    assert not logged_in_client.folder_exists(folder)


@pytest.fixture
def teardown(logged_in_client: IMAPClient):
    teardowns: List[Callable] = []

    yield teardowns

    for func in teardowns:
        for _ in range(3):
            try:
                func(logged_in_client)
            except socket.timeout:
                pass
            else:
                break


def wait_till_mail_appears(client: IMAPClient, uid, timeout=10):
    entry_time = time.time()
    while True:
        if uid in client.search("ALL"):
            break
        if (time.time() - entry_time) > timeout:
            print(f"Waited for {timeout}. Could not find {uid}")
            assert False
        time.sleep(1)


def test_get_server_ssl_error(config: dict, logger, caplog):
    config["ssl"] = True
    with pytest.raises(ssl.SSLError):
        get_client(config, logger, protocol=ssl.PROTOCOL_TLS, verify_cert=True)

    assert "Error due to ssl." in caplog.text


def test_get_server_socket_error(config: dict, logger, caplog):
    config["imap_port"] = 12332  # hopefully random
    with pytest.raises(socket.error):
        get_client(config, logger)

    assert "Could not connect to the mail server." in caplog.text


def test_flag_happy_path(logged_in_client: IMAPClient, random_mail, logger, caplog):
    mark_processed(logged_in_client, random_mail, logger)

    assert random_mail in logged_in_client.get_flags(random_mail)
    assert FLAG_TO_CHECK in logged_in_client.get_flags(random_mail).get(random_mail)
    assert f"Flag added to {random_mail}\n" in caplog.text


def test_flag_if_already_exists(
    logged_in_client: IMAPClient, flagged_random_mail, logger, caplog
):
    mark_processed(logged_in_client, flagged_random_mail, logger)

    assert FLAG_TO_CHECK in logged_in_client.get_flags(flagged_random_mail).get(
        flagged_random_mail
    )
    assert not caplog.text


def test_flag_if_already_exists_with_not_existing_mail_id(
    logged_in_client: IMAPClient, random_mail, logger, caplog, teardown
):

    mail_uid = random_mail + 10

    mark_processed(logged_in_client, mail_uid, logger)

    assert not logged_in_client.get_flags(mail_uid)
    assert f"Mail with uid: {mail_uid} does not exist" in caplog.text


def test_create_folder_if_not_exists_happy_path(
    logged_in_client: IMAPClient, logger, teardown, caplog
):
    random_folder = "random-1234567890"
    assert not logged_in_client.folder_exists(random_folder)

    create_folder_if_not_exists(logged_in_client, random_folder, logger)
    teardown.append(lambda client: client.delete_folder(random_folder))

    assert logged_in_client.folder_exists(random_folder)
    assert not caplog.text


def test_create_folder_if_not_exists_already_exists(
    logged_in_client: IMAPClient, logger, caplog
):
    assert logged_in_client.folder_exists(EmailFolders.INBOX)

    create_folder_if_not_exists(logged_in_client, EmailFolders.INBOX, logger)

    assert logged_in_client.folder_exists(EmailFolders.INBOX)
    assert "Looks like the folder INBOX already exists." in caplog.text


def test_email_shift(
    logged_in_client: IMAPClient, random_folder, random_mail, logger, teardown, caplog
):
    next_uid = logged_in_client.select_folder(random_folder, readonly=True)[b"UIDNEXT"]

    shift_mail(
        client=logged_in_client,
        uid=random_mail,
        source=EmailFolders.INBOX,
        destination=random_folder,
        logger=logger,
    )

    assert f"Email (uid: {random_mail}) moved to {random_folder} folder." in caplog.text

    logged_in_client.select_folder(random_folder, readonly=True)
    assert next_uid in logged_in_client.search("ALL")

    assert SEEN_FLAG not in logged_in_client.get_flags(next_uid)[next_uid]

    logged_in_client.select_folder(EmailFolders.INBOX, readonly=True)
    assert random_mail not in logged_in_client.search("ALL")


def test_email_shift_not_existing_folder(
    logged_in_client: IMAPClient, random_mail, logger, teardown, caplog
):
    not_existing_folder = "random-123322"
    shift_mail(
        client=logged_in_client,
        uid=random_mail,
        source=EmailFolders.INBOX,
        destination=not_existing_folder,
        logger=logger,
    )

    assert (
        f"Failed email (uid: {random_mail}) to move to {not_existing_folder} folder:"
        in caplog.text
    )

    assert not logged_in_client.folder_exists(not_existing_folder)
    # check that message exists in the inbox
    logged_in_client.select_folder(EmailFolders.INBOX, readonly=True)
    assert random_mail in logged_in_client.search("ALL")


def test_process_mails_happy_path_important(
    logged_in_client, random_mail, teardown, logger
):

    next_uid_important = logged_in_client.select_folder(
        EmailFolders.IMPORTANT, readonly=True
    )[b"UIDNEXT"]

    return_value = ProcessedMessage({}, 120, True, False)

    with mock.patch("zippy.client.main.rank_message", return_value=return_value):
        processed_mails = process_mails(logged_in_client, [random_mail], logger)

    def remove_message(client: IMAPClient):
        client.select_folder(EmailFolders.IMPORTANT)
        client.delete_messages(next_uid_important)
        client.expunge()

    teardown.append(remove_message)

    assert len(processed_mails) == 1
    assert random_mail in processed_mails

    # The mail should have been shifted to EmailFolders.IMPORTANT
    logged_in_client.select_folder(EmailFolders.IMPORTANT, readonly=True)
    assert next_uid_important in logged_in_client.search("ALL")

    assert (
        SEEN_FLAG
        not in logged_in_client.get_flags(next_uid_important)[next_uid_important]
    )

    # the old mail should not be in the EmailFolders.INBOX
    logged_in_client.select_folder(EmailFolders.INBOX, readonly=True)
    assert random_mail not in logged_in_client.search("ALL")


def test_process_mails_happy_path_urgent(
    logged_in_client, random_mail, teardown, logger
):

    next_uid_urgent = logged_in_client.select_folder(
        EmailFolders.URGENT, readonly=True
    )[b"UIDNEXT"]

    return_value = ProcessedMessage({}, 120, True, True)

    with mock.patch("zippy.client.main.rank_message", return_value=return_value):
        processed_mails = process_mails(logged_in_client, [random_mail], logger)

    def remove_message(client: IMAPClient):
        client.select_folder(EmailFolders.URGENT)
        client.delete_messages(next_uid_urgent)
        client.expunge()

    teardown.append(remove_message)

    assert len(processed_mails) == 1
    assert random_mail in processed_mails

    # The mail should have been shifted to EmailFolders.IMPORTANT
    logged_in_client.select_folder(EmailFolders.URGENT, readonly=True)
    assert next_uid_urgent in logged_in_client.search("ALL")

    assert SEEN_FLAG not in logged_in_client.get_flags(next_uid_urgent)[next_uid_urgent]

    # the old mail should not be in the EmailFolders.INBOX
    logged_in_client.select_folder(EmailFolders.INBOX, readonly=True)
    assert random_mail not in logged_in_client.search("ALL")


def test_process_mails_happy_path_processed_mark(logged_in_client, random_mail, logger):
    return_value = ProcessedMessage({}, 120, False, False)
    with mock.patch("zippy.client.main.rank_message", return_value=return_value):

        processed_mails = process_mails(logged_in_client, [random_mail], logger)

    assert len(processed_mails) == 1
    assert random_mail in processed_mails

    logged_in_client.select_folder(EmailFolders.INBOX, readonly=True)
    assert FLAG_TO_CHECK in logged_in_client.get_flags(random_mail).get(random_mail)

    assert SEEN_FLAG not in logged_in_client.get_flags(random_mail)[random_mail]


def test_process_mails_fetch_correct_message(logged_in_client, random_mail, logger):
    return_value = ProcessedMessage({}, 120, False, False)
    with mock.patch(
        "zippy.client.main.rank_message", return_value=return_value
    ) as mocked_ranker:
        processed_mails = process_mails(logged_in_client, random_mail, logger)

    assert random_mail in processed_mails

    assert mocked_ranker.call_count == 1
    print(mocked_ranker.mock_calls[0][1][0])
    assert type(mocked_ranker.mock_calls[0][1][0]) == email.message.Message
    assert "Hi there" in mocked_ranker.mock_calls[0][1][0].as_string()

    assert SEEN_FLAG not in logged_in_client.get_flags(random_mail)[random_mail]


def test_retrieve_emails_with_wrong_credentials(
    imap_client: IMAPClient, random_mail, logger, caplog
):
    user = EmailAuthUser("test1@localhost.org", "wrong_password")

    with pytest.raises(LoginError):
        retrieve_new_emails(imap_client, user, logger)

    assert (
        f"Credentials could not be verified for '{user.email_address}'" in caplog.text
    )


def test_retreive_emails_happy_path(
    imap_client: IMAPClient, random_mail, logger, caplog
):
    user = EmailAuthUser("test1@localhost.org", "test1")
    mails = retrieve_new_emails(imap_client, user, logger)

    assert random_mail in mails
    assert f"Logged in successful for {user.email_address}" in caplog.text
