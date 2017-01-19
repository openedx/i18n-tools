"""
This test tests that i18n extraction works properly.
"""
from datetime import datetime, timedelta
import os
import random
import re
import sys
import string
import subprocess

from mock import patch
from polib import pofile
from pytz import UTC

from i18n import config, generate

from . import I18nToolTestCase, MOCK_APPLICATION_DIR, MOCK_DJANGO_APP_DIR


class TestGenerate(I18nToolTestCase):
    """
    Tests functionality of i18n/generate.py
    """

    # This method is suspected of making tests fail as the returncode is happening in a subprocess causing
    # some concurrency issues. If this fails, you can try rerunning the tests.
    @classmethod
    def tearDownClass(cls):
        # Clear the mock locale directory of any test artifacts
        fake_locale_dir = MOCK_APPLICATION_DIR / 'conf' / 'locale' / 'mock'
        cmd = "rm {fake_locale_dir}/LC_MESSAGES/django.po; rm {fake_locale_dir}/LC_MESSAGES/djangojs.po".format(
            fake_locale_dir=fake_locale_dir
        )
        sys.stderr.write("\nCleaning up dummy language directories: {}\n".format(cmd))
        sys.stderr.flush()
        returncode = subprocess.call(cmd, shell=True)
        assert returncode == 0
        super(TestGenerate, cls).tearDownClass()

    def setUp(self):
        super(TestGenerate, self).setUp()
        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now(UTC) - timedelta(seconds=1)

    def test_merge(self):
        """
        Tests merge script on English source files.
        """
        test_configuration = config.Configuration(root_dir=MOCK_DJANGO_APP_DIR)
        filename = os.path.join(test_configuration.source_messages_dir, random_name())
        generate.merge(test_configuration, test_configuration.source_locale, target=filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    # Patch dummy_locales to not have esperanto present
    def test_main(self):
        """
        Runs generate.main() which should merge source files,
        then compile all sources in all configured languages.
        Validates output by checking all .mo files in all configured languages.
        .mo files should exist, and be recently created (modified
        after start of test suite)
        """
        generate.main(verbose=0, strict=False, root_dir=MOCK_APPLICATION_DIR)
        for locale in ['mock',]:
            for (filename, num_headers) in zip(('django', 'djangojs'), (6, 4)):
                mofile = filename + '.mo'
                file_path = os.path.join(self.configuration.get_messages_dir(locale), mofile)
                exists = os.path.exists(file_path)
                self.assertTrue(exists, msg='Missing file in locale %s: %s' % (locale, mofile))
                self.assertTrue(
                    datetime.fromtimestamp(os.path.getmtime(file_path), UTC) >= self.start_time,
                    msg='File should be recently modified: %s' % file_path
                )
            # Assert merge headers look right
            file_path = os.path.join(self.configuration.get_messages_dir(locale), filename + '.po')
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

    @patch('i18n.generate.LOG')
    def test_resolve_merge_conflicts(self, mock_log):
        django_po_path = os.path.join(self.configuration.get_messages_dir('mock'), 'django.po')
        # File ought to have been generated in test_main
        # if not os.path.exists(django_po_path):
        generate.main(verbose=0, strict=False, root_dir=MOCK_APPLICATION_DIR)

        with open(django_po_path, 'r') as django_po_file:
            po_lines = django_po_file.read()

        # check that there are no merge conflicts present
        # "#-#-#-#-#  django-partial.po (edx-platform)  #-#-#-#-#\n"
        pattern = re.compile('\"#-#-#-#-#.*#-#-#-#-#', re.M)
        match = pattern.findall(po_lines)
        self.assertEqual(len(match), 0, msg="Error, found merge conflicts in django.po: %s" % match)
        # Validate that the appropriate log warnings were shown
        self.assertTrue(mock_log.warning.called)
        self.assertIn(
            " %s duplicates in %s, details in .dup file",
            # the first item of call_args is the call arguments themselves as a tuple
            mock_log.warning.call_args[0]
        )


def random_name(size=6):
    """Returns random filename as string, like test-4BZ81W"""
    chars = string.ascii_uppercase + string.digits
    return 'test-' + ''.join(random.choice(chars) for x in range(size))
