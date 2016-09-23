from os import remove
from shutil import copyfile
from unittest import TestCase
import ddt
import mock

from i18n.changed import Changed


@ddt.ddt
class TestChanged(TestCase):
    """
    Tests functionality of i18n/changed.py
    """
    def setUp(self):
        self.changed = Changed()

    def test_detect_changes(self):
        """
        Verifies the detect_changes method can detect changes in translation source files.
        """
        file_name = 'conf/locale/fake2/LC_MESSAGES/mako.po'
        copy = 'conf/locale/fake2/LC_MESSAGES/mako_copy.po'

        self.assertFalse(self.changed.detect_changes())

        copyfile(file_name, copy)  # Copy the .po file
        remove(file_name)  # Make changes to the .po file
        self.assertTrue(self.changed.detect_changes())  # Detect changes made to the .po file
        copyfile(copy, file_name)  # Return .po file to its previous state
        remove(copy)  # Delete copy of .po file

    def test_do_not_detect_changes(self):
        """
        Verifies the detect_changes method doesn't detect changes in rows that do not start with msgid or msgstr.
        """
        file_name = 'test_requirements.txt'
        copy = 'test_requirements_copy.txt'

        copyfile(file_name, copy)  # Copy the .txt file
        remove(file_name)  # Make changes to the .txt file
        self.assertFalse(self.changed.detect_changes())  # Do not detect changes made to the .txt file
        copyfile(copy, file_name)  # Return .txt file to its previous state
        remove(copy)  # Delete copy of .txt file

    @ddt.data(
        (False, 'Source translation files are current.'),
        (True, 'Source translations are out-of-date! Please update them.')
    )
    @ddt.unpack
    def test_get_message(self, changes_detected, msg):
        """
        Verifies that get_message method returns the correct message.
        """
        self.assertEqual(self.changed.get_message(changes_detected), msg)

    @ddt.data(
        (True, 1),
        (False, 0)
    )
    @ddt.unpack
    def test_run(self, return_value, value):
        """
        Verifies that run method returns the correct value.
        """
        with mock.patch('i18n.changed.Changed.detect_changes', mock.Mock(return_value=return_value)):
            self.assertEqual(self.changed.run(''), value)
