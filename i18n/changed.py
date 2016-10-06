#!/usr/bin/env python
"""
Determine if the source translation files are up-to-date.
"""
from __future__ import print_function
from subprocess import CalledProcessError

from i18n import Runner
from i18n.execute import execute


class Changed(Runner):
    """
    Class used to check if the source translation files are up-to-date
    """
    def run(self, args):
        """
        Main entry point of script
        """
        changes_detected = self.detect_changes()
        message = self.get_message(changes_detected)
        print(message)
        return int(changes_detected)

    def detect_changes(self):
        """
        Detect if changes have been made to the msgid or msgstr lines in the translation files.

        Returns:
          boolean: True, if changes detected; otherwise, False.

        Note:
          This method requires ``git`` to be installed on the executing machine.
        """
        try:
            execute('git diff --exit-code -G "^(msgid|msgstr)"')
            return False
        except CalledProcessError:
            return True

    def get_message(self, changes_detected):
        """
        Returns message depending on source translation files status.
        """
        msg = 'Source translation files are current.'

        if changes_detected:
            msg = 'Source translations are out-of-date! Please update them.'

        return msg

main = Changed()  # pylint: disable=invalid-name

if __name__ == '__main__':
    main()
