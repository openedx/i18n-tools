#!/usr/bin/env python
import os
import re

from setuptools import setup


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


def get_version(*file_paths):
     """
     Extract the version string from the file at the given relative path fragments.
     """
     filename = os.path.join(os.path.dirname(__file__), *file_paths)
     version_file = open(filename).read()
     version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
     if version_match:
         return version_match.group(1)
     raise RuntimeError("Unable to find version string.")


VERSION = get_version("i18n", "__init__.py")


setup(
    name='edx-i18n-tools',
    version=VERSION,
    description='edX Internationalization Tools',
    author='edX',
    author_email='oscm@edx.org',
    url='https://github.com/edx/i18n-tools',
    packages=[
        'i18n',
    ],
    install_requires=load_requirements('requirements/base.in'),
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
        'Programming Language :: Python :: 3.8',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
    ],
)
