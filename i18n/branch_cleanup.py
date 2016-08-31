#!/usr/bin/env python
"""
Utility for cleaning up your local directory after switching between
branches with different translation levels (eg master branch, with only
reviewed translations, versus dev branch, with all translations)
"""
from __future__ import print_function

from i18n import config, Runner


def clean_conf_folder(locale):
    """Remove the configuration directory for `locale`"""
    dirname = config.CONFIGURATION.get_messages_dir(locale)
    dirname.removedirs_p()


def clean_configuration_directory():
    """
    Remove the configuration directories for all locales
    in CONFIGURATION.translated_locales
    """
    for locale in config.CONFIGURATION.translated_locales:
        clean_conf_folder(locale)


class BranchCleanup(Runner):
    """
    Class to clean up the branch
    """
    def run(self, args):
        clean_configuration_directory()

main = BranchCleanup()  # pylint: disable=invalid-name

if __name__ == '__main__':
    main()
