#!/usr/bin/env python
"""
Functions to pull down & push up .po files from/to transifex
"""
from __future__ import print_function

import polib
from i18n import config, Runner
from i18n.execute import execute
from i18n.extract import EDX_MARKER

TRANSIFEX_HEADER = u'edX community translations have been downloaded from {}'


def push():
    """
    Push translation source English files to Transifex
    """
    execute('tx push -s')


def pull():
    """
    Pull translations from all languages listed in conf/locale/config.yaml
    where there is at least 10% reviewed translations
    """
    print("Pulling conf/locale/config.yaml:locales from Transifex...")

    for lang in config.CONFIGURATION.translated_locales:
        execute('tx pull --mode=reviewed -l ' + lang)
    clean_translated_locales()


def pull_all():
    """
    Pulls all translations - reviewed or not - for all languages.

    Only cleans locales: listed in conf/locale/config.yaml
    """
    print("Pulling all translations for all languages, reviewed or not, from transifex...")
    execute('tx pull --all')
    clean_translated_locales()


def pull_all_ltr():
    """
    Pulls all translations - reviewed or not - for LTR languages
    """
    print("Pulling all translated LTR languages from transifex...")
    for lang in config.CONFIGURATION.ltr_langs:
        print ('rm -rf conf/locale/' + lang)
        execute('rm -rf conf/locale/' + lang)
        execute('tx pull -l ' + lang)
    clean_translated_locales(langs=config.CONFIGURATION.ltr_langs)


def pull_all_rtl():
    """
    Pulls all translations - reviewed or not - for RTL languages
    """
    print("Pulling all translated RTL languages from transifex...")
    for lang in config.CONFIGURATION.rtl_langs:
        print ('rm -rf conf/locale/' + lang)
        execute('rm -rf conf/locale/' + lang)
        execute('tx pull -l ' + lang)
    clean_translated_locales(langs=config.CONFIGURATION.rtl_langs)


def clean_translated_locales(langs=config.CONFIGURATION.translated_locales):
    """
    Strips out the warning from all translated po files
    about being an English source file.
    """
    for locale in langs:
        clean_locale(locale)


def clean_locale(locale):
    """
    Strips out the warning from all of a locale's translated po files
    about being an English source file.
    Iterates over machine-generated files.
    """
    dirname = config.CONFIGURATION.get_messages_dir(locale)
    for filename in ('django-partial.po', 'djangojs-partial.po', 'mako.po'):
        clean_file(dirname.joinpath(filename))


def clean_file(filename):
    """
    Strips out the warning from a translated po file about being an English source file.
    Replaces warning with a note about coming from Transifex.
    """
    try:
        pofile = polib.pofile(filename)
    except Exception as exc:  # pylint: disable=broad-except
        # An exception can occur when a language is deleted from Transifex.
        # Don't totally fail here.
        print(
            "Encountered error {} with filename {} - language project may "
            "no longer exist on Transifex".format(exc, filename)
        )
        return
    if pofile.header.find(EDX_MARKER) != -1:
        new_header = get_new_header(pofile)
        new = pofile.header.replace(EDX_MARKER, new_header)
        pofile.header = new
        pofile.save()


def get_new_header(pofile):
    """
    Insert info about edX into the po file headers
    """
    team = pofile.metadata.get('Language-Team', None)
    if not team:
        return TRANSIFEX_HEADER.format(config.CONFIGURATION.TRANSIFEX_URL)
    else:
        return TRANSIFEX_HEADER.format(team)


class Transifex(Runner):
    """Define the command class"""
    def add_args(self):
        self.parser.add_argument("command", help="push or pull")

    def run(self, args):
        if args.command == "push":
            push()
        elif args.command == "pull":
            pull()
        elif args.command == "pull_all":
            pull_all()
        elif args.command == "ltr":
            pull_all_ltr()
        elif args.command == "rtl":
            pull_all_rtl()
        else:
            raise Exception("unknown command ({cmd})".format(cmd=args.command))

main = Transifex()  # pylint: disable=invalid-name

if __name__ == '__main__':
    main()
