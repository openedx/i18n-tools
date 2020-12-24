from os import remove
from shutil import copyfile
import ddt
from unittest import mock

from i18n.changed import Changed

from . import I18nToolTestCase, MOCK_APPLICATION_DIR


@ddt.ddt
class TestChanged(I18nToolTestCase):
    """
    Tests functionality of i18n/changed.py
    """
    def setUp(self):
        super().setUp()
        self._setup_i18n_test_config()
        self.changed = Changed()

    def test_detect_changes(self):
        """
        Verifies the detect_changes method can detect changes in translation source files.
        """
        fake_locale_dir = MOCK_APPLICATION_DIR / 'conf' / 'locale' / 'mock'
        file_name = fake_locale_dir / 'LC_MESSAGES' / 'mako.po'
        copy = fake_locale_dir / 'LC_MESSAGES' / 'mako_copy.po'

        # Note: this fails if you have not-yet-committed changes to test fixture .po files
        self.assertFalse(self.changed.detect_changes())

        try:
            copyfile(file_name, copy)  # Copy the .po file
            remove(file_name)  # Make changes to the .po file
            self.assertTrue(self.changed.detect_changes())  # Detect changes made to the .po file
        finally:
            copyfile(copy, file_name)  # Return .po file to its previous state
            remove(copy)  # Delete copy of .po file

    def test_do_not_detect_changes(self):
        """
        Verifies the detect_changes method doesn't detect changes in rows that do not start with msgid or msgstr.
        """
        file_name = 'tests/data/test_do_not_detect_changes.txt'
        copy = 'tests/data/test_do_not_detect_changes_copy.txt'

        try:
            copyfile(file_name, copy)  # Copy the .txt file
            remove(file_name)  # Make changes to the .txt file
            self.assertFalse(self.changed.detect_changes())  # Do not detect changes made to the .txt file
        finally:
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
