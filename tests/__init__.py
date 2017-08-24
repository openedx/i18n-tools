"""
Initialization for unit tests.
"""

from path import Path as path
from unittest import TestCase

from i18n import config

TEST_DATA_DIR = path('.').abspath() / 'tests' / 'data'
MOCK_APPLICATION_DIR = TEST_DATA_DIR / 'mock-application'
MOCK_DJANGO_APP_DIR = TEST_DATA_DIR / 'mock-django-app'


class I18nToolTestCase(TestCase):
    """
    Base class for all i18n tool test cases.
    """
    def setUp(self, root_dir=MOCK_APPLICATION_DIR, preserve_locale_paths=None, clean_paths=None):
        super(I18nToolTestCase, self).setUp()
        self.configuration = config.Configuration(root_dir=root_dir)
        self.preserve_locale_paths = preserve_locale_paths if preserve_locale_paths is not None else []
        self.clean_paths = clean_paths if clean_paths is not None else []

        # Copy off current state of original locale dirs
        for locale_path in self.preserve_locale_paths:
            tmp = self._get_tmp_locale_path(locale_path)
            path.rmtree_p(path(tmp))
            path.copytree(path(locale_path), path(tmp))

    def tearDown(self):
        # Restore previous locale dir state
        for locale_path in self.preserve_locale_paths:
            tmp = self._get_tmp_locale_path(locale_path)
            path.rmtree_p(path(locale_path))
            path.copytree(path(tmp), path(locale_path))
            path.rmtree(path(tmp))

        # Remove any temporary / created paths
        for dirty_path in self.clean_paths:
            path.rmtree_p(path(dirty_path))
            path.rmtree_p(path(self._get_tmp_locale_path(dirty_path)))


    @staticmethod
    def _get_tmp_locale_path(original_path):
        return "{}_tmp".format(original_path)
