#!/usr/bin/env python

from setuptools import setup, find_packages
from pathlib import Path

with open(Path("./README.md").resolve(), 'r') as fh:
    long_description = fh.read()

setup(
    name = "uszparser",
    version = "1.0",
    packages = find_packages(),
    author = "Roman Ludwig",
    author_email = "roman.ludwig@usz.ch",
    description = "Small program for parsing an Excel file of USZ patients.",
    long_description = long_description,
    install_requires = [
        "pandas",
        "numpy",
        "dateutils"
    ],
    python_requires = ">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
