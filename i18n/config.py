import os

import yaml
from path import Path

# BASE_DIR is the working directory to execute django-admin commands from.
# Typically this should be the 'edx-platform' directory.
BASE_DIR = Path('.').abspath()  # pylint: disable=invalid-name

# LOCALE_DIR contains the locale files.
# Typically this should be 'edx-platform/conf/locale'
LOCALE_DIR = BASE_DIR.joinpath('conf', 'locale')


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
    }

    def __init__(self, filename=None):
        self._filename = filename
        self._config = self.read_config(filename)

    def read_config(self, filename):
        """
        Returns data found in config file (as dict), or raises exception if file not found
        """
        if filename is None:
            return {}
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
        return LOCALE_DIR.joinpath(locale, 'LC_MESSAGES')

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

CONFIGURATION = Configuration()
