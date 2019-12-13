#!/usr/bin/env python
"""
Utility for cleaning up your local directory after switching between
branches with different translation levels (eg master branch, with only
reviewed translations, versus dev branch, with all translations)
"""
from __future__ import print_function

from i18n import Runner


class BranchCleanup(Runner):
    """
    Class to clean up the branch
    """
    def run(self, args):
        self.clean_configuration_directory()

    def clean_configuration_directory(self):
        """
        Remove the configuration directories for all locales
        in CONFIGURATION.translated_locales
        """
        for locale in self.configuration.translated_locales:
            self.clean_conf_folder(locale)

    def clean_conf_folder(self, locale):
        """Remove the configuration directory for `locale`"""
        dirname = self.configuration.get_messages_dir(locale)
        dirname.removedirs_p()


main = BranchCleanup()  # pylint: disable=invalid-name

if __name__ == '__main__':
    main()
