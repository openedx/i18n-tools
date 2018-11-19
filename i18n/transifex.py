#!/usr/bin/env python
"""
Functions to pull down & push up .po files from/to transifex
"""
from __future__ import print_function

import polib
from six.moves import input         # pylint: disable=redefined-builtin

from i18n import Runner
from i18n.execute import execute
from i18n.extract import EDX_MARKER

TRANSIFEX_HEADER = u'edX community translations have been downloaded from {}'


def push(*resources):
    """
    Push translation source English files to Transifex.

    Arguments name specific resources to push. Otherwise, push all the source
    files.
    """
    cmd = 'tx push -s'
    if resources:
        for resource in resources:
            execute(cmd + ' -r {resource}'.format(resource=resource))
    else:
        execute(cmd)


def push_all():
    """
    Push translation source English files and all translations to Transifex
    """
    print("\n\nWARNING! This command pushes source AND translations files. Use with caution.\n")
    proceed = input("Are you sure you want to proceed? (Y/n) ")
    if proceed.lower() == 'y':
        # http://docs.transifex.com/client/push/
        # Push source & translation files. Force new resources, continue on errors.
        # Don't require user input (it does it for each resource, so we ask above)
        execute('tx push -s -t --force --skip --no-interactive')
    else:
        print("\n")


def pull(configuration, *resources):
    """
    Pull translations from all languages listed in conf/locale/config.yaml
    where there is at least 10% reviewed translations.

    If arguments are provided, they are specific resources to pull.  Otherwise,
    all resources are pulled.

    """
    print("Pulling conf/locale/config.yaml:locales from Transifex...")

    for lang in configuration.translated_locales:
        cmd = 'tx pull -f --mode=reviewed --minimum-perc=3 -l {lang}'.format(lang=lang)
        if resources:
            for resource in resources:
                execute(cmd + ' -r {resource}'.format(resource=resource))
        else:
            execute(cmd)
    clean_translated_locales(configuration)


def pull_all(configuration):
    """
    Pulls all translations - reviewed or not - for all languages.

    Only cleans locales: listed in conf/locale/config.yaml
    """
    print("Pulling all translations for all languages, reviewed or not, from transifex...")
    execute('tx pull --all')
    clean_translated_locales(configuration)


def pull_all_ltr(configuration):
    """
    Pulls all translations - reviewed or not - for LTR languages
    """
    print("Pulling all translated LTR languages from transifex...")
    for lang in configuration.ltr_langs:
        print('rm -rf conf/locale/' + lang)
        execute('rm -rf conf/locale/' + lang)
        execute('tx pull -l ' + lang)
    clean_translated_locales(configuration, langs=configuration.ltr_langs)


def pull_all_rtl(configuration):
    """
    Pulls all translations - reviewed or not - for RTL languages
    """
    print("Pulling all translated RTL languages from transifex...")
    for lang in configuration.rtl_langs:
        print('rm -rf conf/locale/' + lang)
        execute('rm -rf conf/locale/' + lang)
        execute('tx pull -l ' + lang)
    clean_translated_locales(configuration, langs=configuration.rtl_langs)


def clean_translated_locales(configuration, langs=None):
    """
    Strips out the warning from all translated po files
    about being an English source file.
    """
    if not langs:
        langs = configuration.translated_locales
    for locale in langs:
        clean_locale(configuration, locale)


def clean_locale(configuration, locale):
    """
    Strips out the warning from all of a locale's translated po files
    about being an English source file.
    Iterates over machine-generated files.
    """
    dirname = configuration.get_messages_dir(locale)
    if not dirname.exists():
        # Happens when we have a supported locale that doesn't exist in Transifex
        return
    for filename in dirname.files('*.po'):
        clean_file(configuration, dirname.joinpath(filename))


def clean_file(configuration, filename):
    """
    Strips out the warning from a translated po file about being an English source file.
    Replaces warning with a note about coming from Transifex.
    """
    pofile = polib.pofile(filename)

    if pofile.header.find(EDX_MARKER) != -1:
        new_header = get_new_header(configuration, pofile)
        new = pofile.header.replace(EDX_MARKER, new_header)
        pofile.header = new
        pofile.save()


def get_new_header(configuration, pofile):
    """
    Insert info about edX into the po file headers
    """
    team = pofile.metadata.get('Language-Team', None)
    if not team:
        return TRANSIFEX_HEADER.format(configuration.TRANSIFEX_URL)
    return TRANSIFEX_HEADER.format(team)


class Transifex(Runner):
    """Define the command class"""
    def add_args(self):
        self.parser.add_argument("command", help="push or pull")
        self.parser.add_argument("arg", nargs="*")

    def run(self, args):
        if args.command == "push":
            push(*args.arg)
        elif args.command == "pull":
            pull(self.configuration, *args.arg)
        elif args.command == "pull_all":
            pull_all(self.configuration)
        elif args.command == "ltr":
            pull_all_ltr(self.configuration)
        elif args.command == "rtl":
            pull_all_rtl(self.configuration)
        elif args.command == "push_all":
            push_all()
        else:
            raise Exception("unknown command ({cmd})".format(cmd=args.command))

main = Transifex()  # pylint: disable=invalid-name

if __name__ == '__main__':
    main()
