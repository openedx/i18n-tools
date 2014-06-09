import os
from unittest import TestCase

from i18n import config

class TestConfiguration(TestCase):
    """
    Tests functionality of i18n/config.py
    """

    def test_config(self):
        config_filename = os.path.normpath(os.path.join('tests', 'data', 'config.yaml'))
        cfg = config.Configuration(config_filename)
        self.assertEqual(cfg.source_locale, 'en')

    def test_no_config(self):
        config_filename = os.path.normpath(os.path.join(config.LOCALE_DIR, 'no_such_file'))
        with self.assertRaises(Exception):
            config.Configuration(config_filename)

    def test_valid_configuration(self):
        """
        Make sure we have a valid configuration file,
        and that it contains an 'en' locale.
        Also check values of dummy_locale and source_locale.
        """
        self.assertIsNotNone(config.CONFIGURATION)
        # these will just be defaults
        locales = config.CONFIGURATION.locales
        self.assertIsNotNone(locales)
        self.assertIsInstance(locales, list)
        config_filename = os.path.normpath(os.path.join('tests', 'data', 'config.yaml'))
        config.CONFIGURATION = config.Configuration(config_filename)

        self.assertIn('en', locales)
        self.assertEqual('eo', config.CONFIGURATION.dummy_locales[0])
        self.assertEqual('en', config.CONFIGURATION.source_locale)
