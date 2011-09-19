#/usr/bin/env python
import os
from setuptools import setup, find_packages

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

setup(
    name = "functional_tests",
    description = "Functional test helpers for Django",
    author = "Steven Skoczen",
    author_email = "steven@agoodcloud.com",
    url = "https://github.com/GoodCloud/django-functional-tests",
    version = "0.1",
    packages = find_packages(),
    zip_safe = False,
)