#!/usr/bin/env python

from setuptools import setup

import i18n

setup(
    name='edx-i18n-tools',
    version=i18n.__version__,
    description='edX Internationalization Tools',
    author='edX',
    author_email='oscm@edx.org',
    url='https://github.com/edx/i18n-tools',
    packages=[
        'i18n',
    ],
    install_requires=[
        'django>=1.8,<1.11',
        'polib',
        'path.py>=7.0',
        'pyYaml',
        'six',
    ],
    entry_points={
        'console_scripts': [
            'i18n_tool = i18n.main:main',
        ],
    },
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
    ],
)
