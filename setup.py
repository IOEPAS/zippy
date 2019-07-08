#! /usr/bin/env python
"""Install Zippy."""

from setuptools import setup

NAME = "Zippy"
REQUIRES_PYTHON = ">=3.6.0,<3.7.5"
VERSION = 0.1

METADATA = {
    "name": NAME,
    "version": VERSION,
    "python_requires": REQUIRES_PYTHON,
    "packages": ["zippy"],
}

setup(**METADATA)
