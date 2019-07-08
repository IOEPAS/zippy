"""Tests for parsing email."""
import email

from zippy.pipeline.data.parse_email import get_from_message


def test_message_parsing():
    """Test message parsing."""
    test_email = (
        b"From: test1@email.com\r\n"
        b"Message-ID: <id1@email.com>\r\n"
        b"Subject: Suit up, Ted.\r\n"
        b"To: test2@email.com\r\n"
        b"Date: 05/23/2019\r\n"
        b"Content-Type: multipart/mixed; boundary=000e0cd2dd1216bdff04808328cb\r\n"
        b"This part should be ignored.\r\n"
        b"--000e0cd2dd1216bdff04808328cb\r\n"
        b"Content-Type: text/plain; \r\n"
        b"It's going to be legen, wait for it, dary. Legendary!\r\n"
    )
    test_email_object = email.message_from_bytes(test_email)
    email_dict = get_from_message(test_email_object)

    assert email_dict["Date"] == ["05/23/2019"]
    assert email_dict["From"] == ["test1@email.com"]
    assert email_dict["To"] == ["test2@email.com"]
    assert email_dict["Subject"] == "suit up, ted."
    assert (
        email_dict["content"] == "it's going to be legen, wait for it, dary. legendary!"
    )
