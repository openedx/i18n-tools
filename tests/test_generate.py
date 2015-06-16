"""
This test tests that i18n extraction works properly.
"""
from datetime import datetime, timedelta
import os
import random
import re
import sys
import shutil
import string
import subprocess
from unittest import TestCase

from mock import patch
from path import path
from polib import pofile
from pytz import UTC

from i18n import generate
from i18n.config import CONFIGURATION


class TestGenerate(TestCase):
    """
    Tests functionality of i18n/generate.py
    """

    @classmethod
    def tearDownClass(cls):
        # Clear the fake2 directory of any test artifacts
        cmd = "rm conf/locale/fake2/LC_MESSAGES/django.po; rm conf/locale/fake2/LC_MESSAGES/djangojs.po"
        sys.stderr.write("\nCleaning up dummy language directories: {}\n".format(cmd))
        sys.stderr.flush()
        returncode = subprocess.call(cmd, shell=True)
        assert returncode == 0
        super(TestGenerate, cls).tearDownClass()

    def setUp(self):
        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now(UTC) - timedelta(seconds=1)

    # Patch source_language to be the fake files we already have
    @patch.object(CONFIGURATION, 'source_locale', 'fake2')
    def test_merge(self):
        """
        Tests merge script on English source files.
        """
        filename = os.path.join(CONFIGURATION.source_messages_dir, random_name())
        generate.merge(CONFIGURATION.source_locale, target=filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    # Patch dummy_locales to not have esperanto present
    @patch.object(CONFIGURATION, 'locales', ['fake2'])
    @patch.object(CONFIGURATION, 'source_locale', 'en')
    def test_main(self):
        """
        Runs generate.main() which should merge source files,
        then compile all sources in all configured languages.
        Validates output by checking all .mo files in all configured languages.
        .mo files should exist, and be recently created (modified
        after start of test suite)
        """
        generate.main(verbose=0, strict=False)
        for locale in CONFIGURATION.translated_locales:
            for (filename, num_headers) in zip(('django', 'djangojs'), (6, 4)):
                mofile = filename + '.mo'
                file_path = os.path.join(CONFIGURATION.get_messages_dir(locale), mofile)
                exists = os.path.exists(file_path)
                self.assertTrue(exists, msg='Missing file in locale %s: %s' % (locale, mofile))
                self.assertTrue(
                    datetime.fromtimestamp(os.path.getmtime(file_path), UTC) >= self.start_time,
                    msg='File not recently modified: %s' % file_path
                )
            # Segmenting means that the merge headers don't work they way they
            # used to, so don't make this check for now. I'm not sure if we'll
            # get the merge header back eventually, or delete this code eventually.
            file_path = os.path.join(CONFIGURATION.get_messages_dir(locale), filename + '.po')
            self.assert_merge_headers(file_path, num_headers)

    def assert_merge_headers(self, file_path, num_headers):
        """
        This is invoked by test_main to ensure that it runs after
        calling generate.main().

        There should be exactly num_headers merge comment headers
        in our merged .po file. This counts them to be sure.
        A merge comment looks like this:
        # #-#-#-#-#  django-partial.po (0.1a)  #-#-#-#-#

        """
        pof = pofile(file_path)
        pattern = re.compile('^#-#-#-#-#', re.M)
        match = pattern.findall(pof.header)
        self.assertEqual(
            len(match),
            num_headers,
            msg="Found %s (should be %s) merge comments in the header for %s" % (len(match), num_headers, file_path)
        )

    def test_resolve_merge_conflicts(self):
        django_po_path = os.path.join(CONFIGURATION.get_messages_dir('fake2'), 'django.po')
        # File ought to have been generated in test_main
        if not os.path.exists(django_po_path):
            generate.main(verbose=0, strict=False)

        django_po_file = open(django_po_path, 'r')
        po_lines = django_po_file.read()

        # check that there are no merge conflicts present
        # "#-#-#-#-#  django-partial.po (edx-platform)  #-#-#-#-#\n"
        pattern = re.compile('\"#-#-#-#-#.*#-#-#-#-#', re.M)
        match = pattern.findall(po_lines)
        self.assertEqual(len(match), 0, msg="Error, found merge conflicts in django.po: %s" % match)


def random_name(size=6):
    """Returns random filename as string, like test-4BZ81W"""
    chars = string.ascii_uppercase + string.digits
    return 'test-' + ''.join(random.choice(chars) for x in range(size))
