from datetime import datetime, timedelta
import os
from unittest import skip

import polib
from path import Path

from i18n import extract, config

from . import I18nToolTestCase, MOCK_DJANGO_APP_DIR

# Make sure setup runs only once
SETUP_HAS_RUN = False


@skip('Tests need to be updated to new repo')
class TestExtract(I18nToolTestCase):
    """
    Tests functionality of i18n/extract.py
    """
    generated_files = ('django-partial.po', 'djangojs-partial.po', 'mako.po')

    def setUp(self):
        global SETUP_HAS_RUN

        super(TestExtract, self).setUp()

        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now() - timedelta(seconds=1)

        self.mock_path = Path.joinpath(MOCK_DJANGO_APP_DIR, "locale", "mock")
        self.mock_mapped_path = Path.joinpath(MOCK_DJANGO_APP_DIR, "locale", "mock_mapped")
        self._setup_i18n_test_config(
            root_dir=MOCK_DJANGO_APP_DIR,
            preserve_locale_paths=(self.mock_path, ),
            clean_paths=(self.mock_mapped_path, )
        )
        self.configuration = config.Configuration(root_dir=MOCK_DJANGO_APP_DIR)

        if not SETUP_HAS_RUN:
            # Run extraction script. Warning, this takes 1 minute or more
            extract.main(verbosity=0, config=self.configuration._filename, root_dir=MOCK_DJANGO_APP_DIR)
            SETUP_HAS_RUN = True

    def get_files(self):
        """
        This is a generator.
        Returns the fully expanded filenames for all extracted files
        Fails assertion if one of the files doesn't exist.
        """
        for filename in self.generated_files:
            path = Path.joinpath(self.configuration.source_messages_dir, filename)
            exists = Path.exists(path)
            self.assertTrue(exists, msg='Missing file: %s' % path)
            if exists:
                yield path

    def test_files(self):
        """
        Asserts that each auto-generated file has been modified since 'extract' was launched.
        Intended to show that the file has been touched by 'extract'.
        """
        for path in self.get_files():
            self.assertTrue(datetime.fromtimestamp(os.path.getmtime(path)) > self.start_time,
                            msg='File not recently modified: %s' % path)

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
            self.assertTrue(
                'openedx-translation@googlegroups.com' in header,
                msg='Missing header in %s:\n"%s"' % (path, header)
            )

    def test_metadata(self):
        """Verify all metadata has been modified"""
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            value = metadata['Report-Msgid-Bugs-To']
            expected = 'openedx-translation@googlegroups.com'
            self.assertEquals(expected, value)
