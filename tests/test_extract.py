from datetime import datetime, timedelta
import os
import subprocess
from unittest import TestCase

from nose.plugins.skip import SkipTest
from mock import patch
import polib
from pytz import UTC
import yaml

from i18n import extract, config


# Make sure setup runs only once
SETUP_HAS_RUN = False

class TestExtract(TestCase):
    """
    Tests functionality of i18n/extract.py
    """
    generated_files = ('django-partial.po', 'djangojs-partial.po')

    def setUp(self):
        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now() - timedelta(seconds=1)
        super(TestExtract, self).setUp()

        global SETUP_HAS_RUN
        if not SETUP_HAS_RUN:
            test_config_filename = os.path.normpath(os.path.join('tests', 'data', 'config.yaml'))
            real_config_filename = os.path.normpath(os.path.join('conf', 'locale', 'config.yaml'))
            saved_loc = os.path.normpath(os.path.join('conf', 'locale', 'real_config.yaml'))

            subprocess.call('cp {real} {save}'.format(real=real_config_filename, save=saved_loc), shell=True)
            subprocess.call('cp {test} {real}'.format(test=test_config_filename, real=real_config_filename), shell=True)
            extract.main(verbosity=0)

            SETUP_HAS_RUN = True

    @classmethod
    def tearDownClass(cls):
        saved_loc = os.path.normpath(os.path.join('conf', 'locale', 'real_config.yaml'))
        real_config_filename = os.path.normpath(os.path.join('conf', 'locale', 'config.yaml'))
        subprocess.call('mv {saved} {real}'.format(saved=saved_loc, real=real_config_filename), shell=True)

        super(TestExtract, cls).tearDownClass()

    def get_files(self):
        """
        This is a generator.
        Returns the fully expanded filenames for all extracted files
        Fails assertion if one of the files doesn't exist.
        """
        for filename in self.generated_files:
            path = os.path.join(config.CONFIGURATION.source_messages_dir, filename)
            exists = os.path.exists(path)
            self.assertTrue(exists, msg='Missing file: %s' % filename)
            if exists:
                yield path

    def test_files(self):
        """
        Asserts that each auto-generated file has been modified since 'extract' was launched.
        Intended to show that the file has been touched by 'extract'.
        """

        for path in self.get_files():
            self.assertTrue(datetime.fromtimestamp(os.path.getmtime(path)) > self.start_time,
                            msg='File not recently modified: %s' % os.path.basename(path))

    def test_is_keystring(self):
        """
        Verifies is_keystring predicate
        """
        entry1 = polib.POEntry()
        entry2 = polib.POEntry()
        entry1.msgid = "_.lms.admin.warning.keystring"
        entry2.msgid = "This is not a keystring"
        self.assertTrue(extract.is_key_string(entry1.msgid))
        self.assertFalse(extract.is_key_string(entry2.msgid))

    def test_headers(self):
        """Verify all headers have been modified"""
        for path in self.get_files():
            po = polib.pofile(path)
            header = po.header
            self.assertEqual(
                header.find('edX translation file'),
                0,
                msg='Missing header in %s:\n"%s"' % (os.path.basename(path), header)
            )

    def test_metadata(self):
        """Verify all metadata has been modified"""
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            value = metadata['Report-Msgid-Bugs-To']
            expected = 'openedx-translation@googlegroups.com'
            self.assertEquals(expected, value)
