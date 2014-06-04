#!/usr/bin/env python
from setuptools import setup
import glob, os.path

console_scripts = set()

for mod in glob.glob(os.path.join(os.path.dirname(__file__), 'i18n', '*.py')):
    name = os.path.split(mod)[1].split('.')[0]
    if name not in ('config', '__init__', 'converter', 'execute'):
        console_scripts.add('i18n_{name} = i18n.{name}:main'.format(name=name))

setup(
    name='i18n_tools',
    version='0.1',
    description='edX i18n tools',
    packages=[
        'i18n',
    ],
    install_requires=["polib", "ddt", "path.py", "pyYaml", "pytz"],
    test_suite='nose.collector',
    entry_points={
        'console_scripts': console_scripts
    }
)
