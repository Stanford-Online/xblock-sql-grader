"""
Setup the XBlock
"""
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

def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        with open(path) as reqs:
            requirements.update(
                line.split('#')[0].strip() for line in reqs
                if is_requirement(line.strip())
            )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, a URL, or an included file.
    """
    return line and not line.startswith(('-r', '#', '-e', 'git+', '-c'))

setup(
    name='xblock-sql-grader',
    version='0.0.1',
    description='SQL Grader XBlock',  # TODO: write a better description.
    license='AGPLv3',
    packages=[
        'sql_grader',
    ],
    install_requires=load_requirements('requirements/base.in'),
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
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.8",
    ]
)
