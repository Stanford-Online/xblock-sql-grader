"""
Setup the XBlock
"""
from __future__ import absolute_import

from setuptools import setup
import os


def package_data(pkg, roots):
    """
    Find package_data files

    All of the files under each of the `roots` will be declared as
    package data for package `pkg`
    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))
    return {
        pkg: data,
    }


setup(
    name='xblock-sql-grader',
    version='0.0.1',
    description='SQL Grader XBlock',  # TODO: write a better description.
    license='AGPLv3',
    packages=[
        'sql_grader',
    ],
    install_requires=[
        'Django',
        'XBlock',
        'xblock-utils',
    ],
    entry_points={
        'xblock.v1': [
            'sql_grader = sql_grader.xblocks:SqlGrader',
        ]
    },
    package_data=package_data(
        'sql_grader',
        [
            'datasets/*.sql',
            'scenarios/*.xml',
            'static',
            'templates/*.html',
        ]
    ),
)
