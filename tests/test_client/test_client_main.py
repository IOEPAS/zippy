"""Test client for main client."""
import logging

from unittest.mock import MagicMock, Mock, call

import pytest

from imapclient.exceptions import LoginError
from imapclient.testable_imapclient import TestableIMAPClient

from zippy.client import main


def test_email_auth_user_repr():
    """Test that EmailAuthUser has correct repr."""
    user1 = main.EmailAuthUser("test@email.com", "testpwd")
    assert repr(user1) == "test@email.com"

    user2 = main.EmailAuthUser("test@email.com", "testpwd", "Test")
    assert repr(user2) == "(Test, test@email.com)"

    user3 = main.EmailAuthUser("test@email.com", "testpwd", name="Test")
    assert repr(user3) == "(Test, test@email.com)"


def test_email_auth_user_default_args():
    """Test EmailAuthUser works on default args."""
    user1 = main.EmailAuthUser("test@email.com", password="testpwd")
    assert repr(user1) == "test@email.com"

    user2 = main.EmailAuthUser(email_address="test@email.com", password="testpwd")
    assert repr(user2) == "test@email.com"


def test_get_empty_user():
    """Test get_user returns nothing when empty value is passed."""
    assert main.get_users({"users": []}) == []


def test_get_single_user_without_name():
    """Test correct user passed without name on EmailAuthUser."""
    fixture_without_name = {
        "users": [{"username": "test@email.com", "password": "password"}]
    }

    users = main.get_users(fixture_without_name)
    assert len(users) == 1
    assert isinstance(users[0], main.EmailAuthUser)
    assert users[0].email_address == "test@email.com"
    assert users[0].password == "password"
    assert users[0].name is None


def test_get_single_user_with_name():
    """Test correct user passed with name on EmailAuthUser."""
    fixture_with_name = {
        "users": [
            {
                "username": "test2@email.com",
                "password": "password2",
                "name": "Test User 2",
            }
        ]
    }

    users = main.get_users(fixture_with_name)
    assert len(users) == 1
    assert isinstance(users[0], main.EmailAuthUser)
    assert users[0].email_address == "test2@email.com"
    assert users[0].password == "password2"
    assert users[0].name == "Test User 2"


def test_get_single_user_without_essential_values():
    """Test error without password or email_address for get_user."""
    fixture_without_email = {
        "users": [{"password": "password2", "name": "Test User 2"}]
    }

    with pytest.raises(KeyError) as exc_info:
        main.get_users(fixture_without_email)
    assert str(exc_info.value) == r"'username'"

    fixture_without_password = {"users": [{"username": "user", "name": "Test User 2"}]}

    with pytest.raises(KeyError) as exc_info:
        main.get_users(fixture_without_password)
    assert str(exc_info.value) == r"'password'"


def test_get_multiple_user_without_error():
    """Test for multiple user returned by get_user."""
    fixture_multiple_users = {
        "users": [
            {"username": "test@email.com", "password": "password"},
            {"username": "test2@email.com", "password": "password2"},
        ]
    }

    users = main.get_users(fixture_multiple_users)
    assert len(users) == 2
    assert isinstance(users[0], main.EmailAuthUser), isinstance(
        users[1], main.EmailAuthUser
    )
    assert users[0].email_address == "test@email.com", (
        users[1].email_address == "test2@email.com"
    )
    assert users[0].password == "password", users[1].password == "password2"


def test_get_users_empty_config_raise_error():
    """Test empty data passed returns error."""
    with pytest.raises(KeyError) as exc_info:
        main.get_users({})

    assert str(exc_info.value) == "\"Missing 'users' config inside 'client'\""


def test_with_logging():
    """Test with_logging logs start and completion of job."""
    mocked_logger = MagicMock(logging.Logger)
    calls = [
        call("LOG: Running job %s", "test_func"),
        call("LOG: Job '%s' completed", "test_func"),
    ]

    @main.with_logging(logger=mocked_logger)
    def test_func(w, x, y=2, z=3):  # pylint: disable=invalid-name
        return w, x, y, z

    # test that `test_func` is called (with correct values)
    assert test_func(0, 1, 2) == (0, 1, 2, 3)

    assert mocked_logger.info.call_args_list == calls
    assert mocked_logger.info.call_count == 2


def test_retrieving_new_emails_login_error():
    """Test login error for IMAPClient."""
    server = TestableIMAPClient()
    server._imap.login = Mock()  # pylint: disable=protected-access
    server._imap.login.return_value = (  # pylint: disable=protected-access
        "BAD",
        [b"Something's wrong"],
    )

    with pytest.raises(LoginError):
        main._retrieve_new_emails(  # pylint: disable=protected-access
            server=server, user=main.EmailAuthUser("test0@email.com", "password")
        )
