#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer

with open("README.md", 'r') as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = [line.strip() for line in fh]

setup(
    name = "uszparser",
    version = versioneer.get_version(),
    cmdclass = versioneer.get_cmdclass(),
    packages = find_packages(),
    author = "Roman Ludwig",
    author_email = "roman.ludwig@usz.ch",
    description = "Small program for parsing an Excel file of USZ patients.",
    long_description = long_description,
    install_requires = requirements,
    python_requires = ">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
