import email
import os
import smtplib
import socket
import ssl

from unittest import mock

import pytest

from imapclient import IMAPClient
from imapclient.exceptions import LoginError

from zippy.client.main import (
    MESSAGE_FORMAT,
    EmailAuthUser,
    EmailFolders,
    ProcessedMessage,
    create_folder_if_not_exists,
    get_server,
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
    client = get_server(config, logger)
    yield client
    try:
        client.shutdown()
    except OSError:
        # must have already shutdown
        pass


def test_get_server_ssl_error(config: dict, logger, caplog):
    config["ssl"] = True
    with pytest.raises(ssl.SSLError):
        get_server(config, logger, protocol=ssl.PROTOCOL_TLS, verify_cert=True)

    assert "Error due to ssl." in caplog.text


@pytest.fixture
def random_mail(logged_in_client: IMAPClient, config):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.verify_flags = ssl.CERT_OPTIONAL
    server: smtplib.SMTP = smtplib.SMTP(config["hostname"], config["smtp_port"])
    if config["ssl"]:
        server.starttls(context=ssl_context)
    server.login("test0@localhost.org", "test0")
    message = """\
        Subject: Hi there

    This message is sent from Python."""
    server.sendmail("test0@localhost.org", "test1@localhost.org", message)

    logged_in_client.select_folder(EmailFolders.INBOX)

    uid = logged_in_client.search("ALL")[-1]
    yield uid
    logged_in_client.delete_messages(uid)


@pytest.fixture
def logged_in_client(config, logger):
    client = get_server(config, logger)
    client.login("test1@localhost.org", "test1")
    yield client
    client.logout()
    try:
        client.shutdown()
    except OSError:
        # already shutdown
        pass


@pytest.fixture
def flagged_random_mail(logged_in_client: IMAPClient, random_mail):
    logged_in_client.add_flags(random_mail, b"processed")
    assert b"processed" in logged_in_client.get_flags(random_mail).get(random_mail)
    yield random_mail


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
    teardowns = []

    yield teardowns

    for func in teardowns:
        for i in range(2):
            try:
                func(logged_in_client)
            except socket.timeout:
                pass
            else:
                break


def test_get_server_socket_error(config: dict, logger, caplog):
    config["imap_port"] = 12332  # hopefully random
    with pytest.raises(socket.error):
        get_server(config, logger)

    assert "Could not connect to the mail server." in caplog.text


def test_flag_happy_path(
    logged_in_client: IMAPClient, random_mail, logger, caplog, teardown
):
    mark_processed(logged_in_client, random_mail, logger)

    assert random_mail in logged_in_client.get_flags(random_mail)
    assert b"processed" in logged_in_client.get_flags(random_mail).get(random_mail)
    assert f"Flag added to {random_mail}\n" in caplog.text


def test_flag_if_already_exists(
    logged_in_client: IMAPClient, flagged_random_mail, logger, caplog, teardown
):
    mark_processed(logged_in_client, flagged_random_mail, logger)

    assert b"processed" in logged_in_client.get_flags(flagged_random_mail).get(
        flagged_random_mail
    )


def test_flag_if_already_exists_with_random_mail(
    logged_in_client: IMAPClient, random_mail, logger, caplog, teardown
):

    mark_processed(logged_in_client, 12222222, logger)

    assert not logged_in_client.get_flags(12222222)
    assert "Mail with uid: 12222222 does not exist" in caplog.text


def test_create_folder_if_not_exists_happy_path(
    logged_in_client: IMAPClient, logger, teardown, caplog
):
    assert not logged_in_client.folder_exists("random")

    create_folder_if_not_exists(logged_in_client, "random", logger)
    teardown.append(lambda client: client.delete_folder("random"))

    assert logged_in_client.folder_exists("random")
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
    logged_in_client.select_folder(random_folder)
    assert not logged_in_client.search("ALL")

    shift_mail(logged_in_client, random_mail, random_folder, logger)

    logged_in_client.select_folder(random_folder)
    mails = logged_in_client.search("ALL")

    # change folder, so that when teardown occurs, different folder gets deleted
    # and, connection is not aborted
    logged_in_client.select_folder(EmailFolders.INBOX)

    assert random_mail not in logged_in_client.search("ALL")
    assert len(mails) == 1

    assert f"Email (uid: {random_mail}) moved to {random_folder} folder." in caplog.text


def test_email_shift_random(
    logged_in_client: IMAPClient, random_mail, logger, teardown, caplog
):
    shift_mail(logged_in_client, random_mail, "random-123322", logger)

    assert (
        f"Failed email (uid: {random_mail}) to move to random-123322 folder:"
        in caplog.text
    )

    assert not logged_in_client.folder_exists("random-123322")
    # check that message exists in the inbox
    assert random_mail in logged_in_client.fetch(random_mail, MESSAGE_FORMAT)


def test_process_mails_happy_path_important(logged_in_client, random_mail, logger):
    return_value = ProcessedMessage({}, 120, True, False)

    msg_data = logged_in_client.fetch([random_mail], MESSAGE_FORMAT)[random_mail]
    prev_mail: email.message.EmailMessage = email.message_from_bytes(
        msg_data[MESSAGE_FORMAT]
    )

    with mock.patch("zippy.client.main.rank_message", return_value=return_value):
        processed_mails = process_mails(logged_in_client, [random_mail], logger)

    assert len(processed_mails) == 1
    assert random_mail in processed_mails

    # The mail should have been shifted to EmailFolders.IMPORTANT
    logged_in_client.select_folder(EmailFolders.IMPORTANT)
    last_mail = logged_in_client.search("ALL")[-1]
    msg_data = logged_in_client.fetch(last_mail, MESSAGE_FORMAT)[last_mail]
    shifted_mail: email.message.EmailMessage = email.message_from_bytes(
        msg_data[MESSAGE_FORMAT]
    )

    assert prev_mail.get("date") == shifted_mail.get("date")

    # the old mail should not be in the EmailFolders.INBOX
    logged_in_client.select_folder(EmailFolders.INBOX)
    assert random_mail not in logged_in_client.search("ALL")


def test_process_mails_happy_path_urgent(logged_in_client, random_mail, logger):
    return_value = ProcessedMessage({}, 120, True, True)

    msg_data = logged_in_client.fetch([random_mail], MESSAGE_FORMAT)[random_mail]
    prev_mail: email.message.EmailMessage = email.message_from_bytes(
        msg_data[MESSAGE_FORMAT]
    )

    with mock.patch("zippy.client.main.rank_message", return_value=return_value):
        processed_mails = process_mails(logged_in_client, [random_mail], logger)

    assert len(processed_mails) == 1
    assert random_mail in processed_mails

    # The mail should have been shifted to EmailFolders.IMPORTANT
    logged_in_client.select_folder(EmailFolders.URGENT)
    last_mail = logged_in_client.search("ALL")[-1]
    msg_data = logged_in_client.fetch(last_mail, MESSAGE_FORMAT)[last_mail]
    shifted_mail: email.message.EmailMessage = email.message_from_bytes(
        msg_data[MESSAGE_FORMAT]
    )

    assert prev_mail.get("date") == shifted_mail.get("date")

    # the old mail should not be in the EmailFolders.INBOX
    logged_in_client.select_folder(EmailFolders.INBOX)
    assert random_mail not in logged_in_client.search("ALL")


def test_process_mails_happy_path_processed_mark(logged_in_client, random_mail, logger):
    return_value = ProcessedMessage({}, 120, False, False)
    with mock.patch("zippy.client.main.rank_message", return_value=return_value):

        processed_mails = process_mails(logged_in_client, [random_mail], logger)

    assert random_mail in processed_mails

    logged_in_client.select_folder(EmailFolders.INBOX)
    assert b"processed" in logged_in_client.get_flags(random_mail).get(random_mail)


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
