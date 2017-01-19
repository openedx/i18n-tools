"""
Unit tests for i18n configuration handling.
"""

import ddt
import os

from i18n import config

from . import I18nToolTestCase, MOCK_APPLICATION_DIR, MOCK_DJANGO_APP_DIR


@ddt.ddt
class TestConfiguration(I18nToolTestCase):
    """
    Tests functionality of i18n/config.py
    """

    def test_config(self):
        config_filename = os.path.normpath(os.path.join('tests', 'data', 'config.yaml'))
        cfg = config.Configuration(config_filename)
        self.assertEqual(cfg.source_locale, 'en')

    def test_no_config(self):
        config_filename = os.path.normpath(os.path.join(config.BASE_DIR, 'no_such_file'))
        with self.assertRaises(Exception):
            config.Configuration(config_filename)

    @ddt.data(
        MOCK_APPLICATION_DIR,
        MOCK_DJANGO_APP_DIR,
    )
    def test_default_configuration(self, root_dir):
        """
        Make sure we have a valid defaults in the configuration file:
        that it contains an 'en' locale, has values for dummy_locale,
        source_locale, and others.
        """
        test_configuration = config.Configuration(root_dir=root_dir)
        self.assertIsNotNone(test_configuration)
        # these will just be defaults
        locales = test_configuration.locales
        self.assertIsNotNone(locales)
        self.assertIsInstance(locales, list)
        self.assertEqual(
            'https://www.transifex.com/open-edx/edx-platform/',
            test_configuration.TRANSIFEX_URL
        )

    def test_configuration_overrides(self):
        # Test overriding the default configuration, and that overrides
        # values are recognized
        config_filename = os.path.normpath(os.path.join('tests', 'data', 'config.yaml'))
        test_configuration = config.Configuration(config_filename)
        locales = test_configuration.locales

        self.assertIn('ar', locales)
        self.assertEqual('eo', test_configuration.dummy_locales[0])
        self.assertEqual('en', test_configuration.source_locale)
        self.assertEqual(
            'https://www.transifex.com/open-edx-releases/cypress-release/',
            test_configuration.TRANSIFEX_URL
        )
