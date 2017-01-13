"""
Initialization for unit tests.
"""

from path import Path
from unittest import TestCase

from i18n import config

TEST_DATA_DIR = Path('.').abspath() / 'tests' / 'data'
MOCK_APPLICATION_DIR = TEST_DATA_DIR / 'mock-application'
MOCK_DJANGO_APP_DIR = TEST_DATA_DIR / 'mock-django-app'


class I18nToolTestCase(TestCase):
    """
    Base class for all i18n tool test cases.
    """
    def setUp(self):
        super(I18nToolTestCase, self).setUp()
        self.configuration = config.Configuration(root_dir=MOCK_APPLICATION_DIR)
