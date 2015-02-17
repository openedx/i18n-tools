#!/usr/bin/env python
import importlib
import sys
# Possibly a Pylint bug in the most recent version that causes it to not recognize module members
from path import path  # pylint: disable=no-name-in-module


def get_valid_commands():
    modules = [m.basename().split('.')[0] for m in path(__file__).dirname().files('*.py')]
    commands = []
    for modname in modules:
        if modname == 'main':
            continue
        mod = importlib.import_module('i18n.%s' % modname)
        if hasattr(mod, 'main'):
            commands.append(modname)
    return commands


def error_message():
    sys.stderr.write('valid commands:\n')
    for cmd in get_valid_commands():
        sys.stderr.write('\t%s\n' % cmd)
    return -1


def main():
    try:
        command = sys.argv[1]
    except IndexError:
        return error_message()

    try:
        module = importlib.import_module('i18n.%s' % command)
        module.main.args = sys.argv[2:]
    except (ImportError, AttributeError):
        return error_message()

    return module.main()

if __name__ == '__main__':
    sys.exit(main())
