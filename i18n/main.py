#!/usr/bin/env python
"""
Main function for internationalization tools.
"""
import importlib
import sys

from path import Path


def get_valid_commands():
    """
    Returns valid commands.

    Returns:
        commands (list): List of valid commands
    """
    modules = [m.basename().split('.')[0] for m in Path(__file__).dirname().files('*.py')]
    commands = []
    for modname in modules:
        if modname == 'main':
            continue
        mod = importlib.import_module('i18n.%s' % modname)
        if hasattr(mod, 'main'):
            commands.append(modname)
    return commands


def error_message():
    """
    Writes out error message specifying the valid commands.

    Returns:
        Failure code for system exit
    """
    sys.stderr.write('valid commands:\n')
    for cmd in get_valid_commands():
        sys.stderr.write('\t%s\n' % cmd)
    return -1


def main():
    """
    Executes the given command. Returns error_message if command is not valid.

    Returns:
        Output of the given command or error message if command is not valid.
    """
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
