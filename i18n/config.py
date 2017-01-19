"""
Reads configuration specifications.
"""
import os

import yaml
from path import Path

# BASE_DIR is the working directory to execute django-admin commands from.
# Typically this should be the 'edx-platform' directory.
BASE_DIR = Path('.').abspath()  # pylint: disable=invalid-name

# The base filename for the configuration file.
BASE_CONFIG_FILENAME = 'config.yaml'


class Configuration(object):
    """
    Reads localization configuration in json format.
    """
    DEFAULTS = {
        'dummy_locales': [],
        'generate_merge': {},
        'ignore_dirs': [],
        'locales': ['en'],
        'segment': {},
        'source_locale': 'en',
        'third_party': [],
        'TRANSIFEX_URL': 'https://www.transifex.com/open-edx/edx-platform/',
    }

    def __init__(self, filename=None, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else Path('.')
        self._filename = (Path(filename) if filename else Configuration.default_config_filename(root_dir=root_dir))
        self._config = self.read_config(self._filename)

    @property
    def locale_dir(self):
        """
        Returns the locale directory for this configuration.
        """
        return self._filename.parent

    @staticmethod
    def default_config_filename(root_dir=None):
        """
        Returns the default name of the configuration file.
        """
        root_dir = Path(root_dir) if root_dir else Path('.').abspath()
        locale_dir = root_dir / 'locale'
        if not os.path.exists(locale_dir):
            locale_dir = root_dir / 'conf' / 'locale'
        return locale_dir / BASE_CONFIG_FILENAME

    def read_config(self, filename):
        """
        Returns data found in config file (as dict), or raises exception if file not found
        """
        if not os.path.exists(filename):
            raise Exception("Configuration file cannot be found: %s" % filename)
        with open(filename) as stream:
            return yaml.safe_load(stream)

    def __getattr__(self, name):
        if name in self.DEFAULTS:
            return self._config.get(name, self.DEFAULTS[name])
        raise AttributeError("Configuration has no such setting: {!r}".format(name))

    def get_messages_dir(self, locale):
        """
        Returns the name of the directory holding the po files for locale.
        Example: edx-platform/conf/locale/fr/LC_MESSAGES
        """
        return self.locale_dir.joinpath(locale, 'LC_MESSAGES')

    @property
    def source_messages_dir(self):
        """
        Returns the name of the directory holding the source-language po files (English).
        Example: edx-platform/conf/locale/en/LC_MESSAGES
        """
        return self.get_messages_dir(self.source_locale)

    @property
    def translated_locales(self):
        """
        Returns the set of locales to be translated (ignoring the source_locale).
        """
        return sorted(set(self.locales) - set([self.source_locale]))

    @property
    def rtl_langs(self):
        """
        Returns the set of translated RTL language codes present in self.locales.
        Ignores source locale.
        """
        def is_rtl(lang):
            """
            Returns True if lang is a RTL language

            args:
                lang (str): The language to be checked

            Returns:
                True if lang is an RTL language.
            """
            # Base RTL langs are Arabic, Farsi, Hebrew, and Urdu
            base_rtl = ['ar', 'fa', 'he', 'ur']

            # do this to capture both 'fa' and 'fa_IR'
            return any([lang.startswith(base_code) for base_code in base_rtl])

        return sorted(set([lang for lang in self.translated_locales if is_rtl(lang)]))

    @property
    def ltr_langs(self):
        """
        Returns the set of translated LTR language codes present in self.locales.
        Ignores source locale.
        """
        return sorted(set(self.translated_locales) - set(self.rtl_langs))

CONFIGURATION = None
