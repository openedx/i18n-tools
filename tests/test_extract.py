import os
from datetime import datetime, timedelta
from functools import wraps

import polib
from i18n import extract, config
from path import Path

from . import I18nToolTestCase, MOCK_DJANGO_APP_DIR


def perform_extract():
    """
    Decorator for test methods in TestExtract class.
    """
    def decorator(test_method):
        """
        The decorator itself
        """
        @wraps(test_method)
        def wrapped(self):
            """
            The wrapper function
            """
            extract.main(
                verbosity=0,
                config=self.configuration._filename,
                root_dir=MOCK_DJANGO_APP_DIR,
            )
            test_method(self)
        return wrapped
    return decorator


class TestExtract(I18nToolTestCase):
    """
    Tests functionality of i18n/extract.py
    """
    def setUp(self):
        super().setUp()

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

    @property
    def django_po(self):
        """
        Returns the name of the generated django file
        """
        return 'django-partial.po'

    @property
    def djangojs_po(self):
        """
        Returns the name of the generated djangojs file
        """
        return 'djangojs-partial.po'

    def get_files(self):
        """
        This is a generator.
        Returns the fully expanded filenames for all extracted files
        Fails assertion if one of the files doesn't exist.
        """
        generated_files = ('mako.po', self.django_po, self.djangojs_po,)

        for filename in generated_files:
            path = Path.joinpath(self.configuration.source_messages_dir, filename)
            exists = Path.exists(path)
            self.assertTrue(exists, msg='Missing file: %s' % path)

            yield path

    @perform_extract()
    def test_files(self):
        """
        Asserts that each auto-generated file has been modified since 'extract' was launched.
        Intended to show that the file has been touched by 'extract'.
        """
        for path in self.get_files():
            self.assertTrue(datetime.fromtimestamp(os.path.getmtime(path)) > self.start_time,
                            msg='File not recently modified: %s' % path)

    @perform_extract()
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

    @perform_extract()
    def test_headers(self):
        """
        Verify all headers have been modified
        """
        for path in self.get_files():
            po = polib.pofile(path)
            header = po.header
            self.assertTrue(
                'openedx-translation@googlegroups.com' in header,
                msg='Missing header in %s:\n"%s"' % (path, header)
            )

    @perform_extract()
    def test_metadata(self):
        """
        Verify all metadata has been modified
        """
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            value = metadata['Report-Msgid-Bugs-To']
            expected = 'openedx-translation@googlegroups.com'
            self.assertEquals(expected, value)

    @perform_extract()
    def test_metadata_no_create_date(self):
        """
        Verify `POT-Creation-Date` metadata has been removed
        """
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            self.assertIsNone(metadata.get('POT-Creation-Date'))
