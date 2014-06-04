#!/usr/bin/env python
import importlib
import sys

def main():
    try:
        command = sys.argv[1]
    except IndexError:
        sys.stderr.write('must specify a command\n')
        return -1
    module = importlib.import_module('i18n.%s' % command)
    module.main.args = sys.argv[2:]
    return module.main()

if __name__ == '__main__':
    sys.exit(main())
