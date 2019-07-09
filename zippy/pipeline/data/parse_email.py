"""Module to parse email."""

import re


def get_text_from_email(msg):
    """Extract text from message object."""
    parts = []
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            parts.append(part.get_payload())
    return str.lower("".join(parts))


def get_from_message(message):
    """Parse raw email from message object."""
    msg = {}
    keys = message.keys()
    for key in keys:
        msg[key] = [str.lower(message[key])]
    msg["content"] = get_text_from_email(message)
    msg["From"] = [re.search(r"[\w_\-\.]+@[\w_\-\.]+\.[\w]+", msg["From"][0]).group(0)]
    msg["is_thread"] = len(msg["Subject"][0].split("re: ")) > 1
    msg["Subject"] = msg["Subject"][0].strip("re: ")
    return msg
