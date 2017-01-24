#!/usr/bin/env python
from distutils.core import setup
import os

if 'CIRCLE_TAG' in os.environ:
    version = os.environ['CIRCLE_TAG']
else:
    if 'CI' in os.environ:
        buildnum = os.environ['CIRCLE_BUILD_NUM']
    else:
        buildnum = "DEV"
    version = "1.9.{build}".format(build=buildnum)

setup(
    name="gnmvidispine",
    version=version,
    description="An object-oriented Python interface to the Vidispine Media Asset Management system",
    author="Andy Gallagher",
    author_email="andy.gallagher@theguardian.com",
    url="https://github.com/fredex42/gnmvidispine",
    packages=['gnmvidispine']
)