#!/usr/bin/env python

from setuptools import setup

setup(
    name='i18n_tools',
    version='0.3.2',
    description='edX i18n tools',
    packages=[
        'i18n',
    ],
    install_requires=["polib", "ddt", "path.py", "pyYaml", "pytz"],
    tests_require=["rednose"],
    test_suite='nose.collector',
    entry_points={
        'console_scripts': [
            'i18n_tool = i18n.main:main',
        ],
    },
)
