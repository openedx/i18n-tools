import os
from datetime import datetime, timedelta
from functools import wraps
import itertools

import ddt
import mock
import polib
from i18n import extract, config
from path import Path

from . import I18nToolTestCase, MOCK_DJANGO_APP_DIR


def perform_extract_with_options():
    """
    Decorator for test methods in TestExtract class.

    It wraps the test method in a function that calls (extract.main) with various options using (ddt.data)

    Sets the following attributes:
    - ddt_flag_merge_po_files: True if the test method should be run with merge-po-files=True
    - ddt_flag_no_segment: True if the test method should be run with no-segment=True
    """
    def decorator(test_method):
        """
        The decorator itself
        """
        @wraps(test_method)
        @ddt.data(*itertools.product([True, False], repeat=2))   # all combinations of flags
        @ddt.unpack
        def wrapped(self, flag_merge_po_files, flag_no_segment):
            """
            The wrapper function
            """
            self.ddt_flag_merge_po_files = flag_merge_po_files
            self.ddt_flag_no_segment = flag_no_segment
            extract.main(
                verbosity=0,
                config=self.configuration._filename,
                root_dir=MOCK_DJANGO_APP_DIR,
                merge_po_files=flag_merge_po_files,
                no_segment=flag_no_segment,
            )
            test_method(self)
        return wrapped
    return decorator


class ExtractInitTestMixin(I18nToolTestCase):
    """
    Mixin for that initializes the test environment for testing extract functionality
    """
    def setUp(self):
        """
        Initialize the test environment
        """
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

        # These will be set by extract_options decorator. Also get_files will fail if they are None (to remind us
        # to use the decorator in all tests methods)
        self.ddt_flag_merge_po_files = None
        self.ddt_flag_no_segment = None


@ddt.ddt
class TestExtract(ExtractInitTestMixin):
    """
    Tests functionality of i18n/extract.py
    """
    @property
    def django_po(self):
        """
        Returns file or partial file name according to the no-segment flag
        """
        return extract.DJANGO_PO if self.ddt_flag_no_segment else extract.DJANGO_PARTIAL_PO

    @property
    def djangojs_po(self):
        """
        Returns jsfile or partial jsfile name according to the no-segment flag
        """
        return extract.DJANGOJS_PO if self.ddt_flag_no_segment else extract.DJANGOJS_PARTIAL_PO

    def get_files(self):
        """
        This is a generator.
        Returns the fully expanded filenames for all extracted files
        Fails assertion if one of the files doesn't exist.
        """
        assert self.ddt_flag_merge_po_files is not None, "Use perform_extract decorator"
        assert self.ddt_flag_no_segment is not None, "Use perform_extract decorator"

        # Depending on how the merge-po-files and no-segment options are set, we may have generated different files
        # no-segment: no partial files are generated, because they replaced the original django.po and djangojs.po
        # merge-po-files: no djangojs*.po is generated, because it has been merged into django*.po
        generated_files = (self.django_po,)
        if not self.ddt_flag_merge_po_files:
            generated_files += (self.djangojs_po,)

        for filename in generated_files:
            path = Path.joinpath(self.configuration.source_messages_dir, filename)
            exists = Path.exists(path)
            self.assertTrue(exists, msg='Missing file: %s' % path)

            yield path

    def is_file_generated(self, file_path):
        """
        Helper to check if the given file has been generated or not

        Using only (Path.exists) is misleading because all possible files are already exist at the beginning
        of the test. Therefore, we need to check the file's modification time too
        """
        if not Path.exists(file_path):
            return False
        return datetime.fromtimestamp(os.path.getmtime(file_path)) > self.start_time

    @perform_extract_with_options()
    def test_files(self):
        """
        Asserts that each auto-generated file has been modified since 'extract' was launched.
        Intended to show that the file has been touched by 'extract'.
        """
        for path in self.get_files():
            self.assertTrue(self.is_file_generated(path), msg='File not recently modified: %s' % path)

    @perform_extract_with_options()
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

    @perform_extract_with_options()
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

    @perform_extract_with_options()
    def test_metadata(self):
        """
        Verify all metadata has been modified
        """
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            value = metadata['Report-Msgid-Bugs-To']
            expected = 'openedx-translation@googlegroups.com'
            self.assertEqual(expected, value)

    @perform_extract_with_options()
    def test_metadata_fixed_creation_and_revision_dates(self):
        """
        Verify `POT-Creation-Date` and `PO-Revision-Date` metadata are always set to a fixed date-time
        """
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            self.assertEqual(metadata.get('POT-Creation-Date'), '2023-06-13 08:00+0000')
            self.assertEqual(metadata.get('PO-Revision-Date'), '2023-06-13 09:00+0000')

    @perform_extract_with_options()
    def test_merge_po_files(self):
        """
        Verify that djangojs*.po is generated only if merge-po-files is not set
        """
        assert self.ddt_flag_merge_po_files != self.is_file_generated(
            Path.joinpath(self.configuration.source_messages_dir, self.djangojs_po,)
        )

    @perform_extract_with_options()
    def test_no_segment_guard_to_verify_names_in_tests(self):
        """
        Verify that (django_po) and (djangojs_po) properties return the correct file names
        according to no-segment flag
        """
        assert self.ddt_flag_no_segment != ('-partial' in self.django_po)
        assert self.ddt_flag_no_segment != ('-partial' in self.djangojs_po)

    @perform_extract_with_options()
    def test_no_segment_partial_files(self):
        """
        Verify that partial files are not generated if no-segment is True
        """
        # We can't use (django_po) and (djangojs_po) properties here because we need to always check
        # for (partial) files
        assert self.ddt_flag_no_segment != self.is_file_generated(
            Path.joinpath(self.configuration.source_messages_dir, extract.DJANGO_PARTIAL_PO,)
        )
        if not self.ddt_flag_merge_po_files:
            assert self.ddt_flag_no_segment != self.is_file_generated(
                Path.joinpath(self.configuration.source_messages_dir, extract.DJANGOJS_PARTIAL_PO,)
            )

    def test_no_segment_off_do_call_segment_pofiles(self):
        """
        Verify that (segment_pofiles) is called if no-segment is False
        """
        with mock.patch('i18n.extract.segment_pofiles') as mock_segment_pofiles:
            extract.main(
                verbosity=0,
                config=self.configuration._filename,
                root_dir=MOCK_DJANGO_APP_DIR,
                no_segment=False,
            )
        mock_segment_pofiles.assert_called_once()

    def test_no_segment_on_dont_call_segment_pofiles(self):
        """
        Verify that (segment_pofiles) is not called if no-segment is True
        """
        with mock.patch('i18n.extract.segment_pofiles') as mock_segment_pofiles:
            extract.main(
                verbosity=0,
                config=self.configuration._filename,
                root_dir=MOCK_DJANGO_APP_DIR,
                no_segment=True,
            )
        mock_segment_pofiles.assert_not_called()
