"""Tests that validate .po files."""
from __future__ import print_function

import codecs
import logging
import os
import sys
import textwrap

import polib

from i18n.execute import call
from i18n.converter import Converter
from i18n import Runner, config

log = logging.getLogger(__name__)


def validate_po_files(root, report_empty=False):
    """
    Validate all of the po files found in the root directory.
    """

    for dirpath, __, filenames in os.walk(root):
        for name in filenames:
            __, ext = os.path.splitext(name)
            if ext.lower() == '.po':
                filename = os.path.join(dirpath, name)
                # First validate the format of this file
                msgfmt_check_po_file(filename)
                # Now, check that the translated strings are valid, and optionally check for empty translations
                check_messages(filename, report_empty)


def msgfmt_check_po_file(filename):
    """
    Call GNU msgfmt -c on each .po file to validate its format.
    Any errors caught by msgfmt are logged to log.
    """
    # Use relative paths to make output less noisy.
    rfile = os.path.relpath(filename, config.LOCALE_DIR)
    out, err = call('msgfmt -c {}'.format(rfile), working_directory=config.LOCALE_DIR)
    if err != '':
        log.info('\n' + out)
        log.warn('\n' + err)


def tags_in_string(msg):
    """
    Return the set of tags in a message string.

    Tags includes HTML tags, data placeholders, etc.

    Skips tags that might change due to translations: HTML entities, <abbr>,
    and so on.

    """
    def is_linguistic_tag(tag):
        """Is this tag one that can change with the language?"""
        if tag.startswith("&"):
            return True
        if any(x in tag for x in ["<abbr>", "<abbr ", "</abbr>"]):
            return True
        return False

    __, tags = Converter().detag_string(msg)
    return set(t for t in tags if not is_linguistic_tag(t))


def astral(msg):
    """Does `msg` have characters outside the Basic Multilingual Plane?"""
    return any(ord(c) > 0xFFFF for c in msg)


def check_messages(filename, report_empty=False):
    """
    Checks messages in various ways:

    Translations must have the same slots as the English. Messages can't have astral
    characters in them.

    If report_empty is True, will also report empty translation strings.

    """
    # Don't check English files.
    if "/locale/en/" in filename:
        return

    # problems will be a list of tuples.  Each is a description, and a msgid,
    # and then zero or more translations.
    problems = []
    pomsgs = polib.pofile(filename)
    for msg in pomsgs:
        # Check for characters Javascript can't support.
        # https://code.djangoproject.com/ticket/21725
        if astral(msg.msgstr):
            problems.append(("Non-BMP char", msg.msgid, msg.msgstr))

        if msg.msgid_plural:
            # Plurals: two strings in, N strings out.
            source = msg.msgid + " | " + msg.msgid_plural
            translation = " | ".join(v for k, v in sorted(msg.msgstr_plural.items()))
            empty = any(not t.strip() for t in msg.msgstr_plural.values())
        else:
            # Singular: just one string in and one string out.
            source = msg.msgid
            translation = msg.msgstr
            empty = not msg.msgstr.strip()

        if empty:
            if report_empty:
                problems.append(("Empty translation", source))
        else:
            id_tags = tags_in_string(source)
            tx_tags = tags_in_string(translation)

            # Check if tags don't match
            if id_tags != tx_tags:
                id_has = u", ".join(u'"{}"'.format(t) for t in id_tags - tx_tags)
                tx_has = u", ".join(u'"{}"'.format(t) for t in tx_tags - id_tags)
                if id_has and tx_has:
                    diff = u"{} vs {}".format(id_has, tx_has)
                elif id_has:
                    diff = u"{} missing".format(id_has)
                else:
                    diff = u"{} added".format(tx_has)
                problems.append((
                    "Different tags in source and translation",
                    source,
                    translation,
                    diff
                ))

    if problems:
        problem_file = filename.replace(".po", ".prob")
        id_filler = textwrap.TextWrapper(width=79, initial_indent="  msgid: ", subsequent_indent=" " * 9)
        tx_filler = textwrap.TextWrapper(width=79, initial_indent="  -----> ", subsequent_indent=" " * 9)
        with codecs.open(problem_file, "w", encoding="utf8") as prob_file:
            for problem in problems:
                desc, msgid = problem[:2]
                prob_file.write(u"{}\n{}\n".format(desc, id_filler.fill(msgid)))
                for translation in problem[2:]:
                    prob_file.write(u"{}\n".format(tx_filler.fill(translation)))
                prob_file.write(u"\n")

        log.error(" %s problems in %s, details in .prob file", len(problems), filename)
    else:
        log.info(" No problems found in %s", filename)


class Validate(Runner):
    def add_args(self):
        self.parser.description = "Automatically finds translation errors in all edx-platform *.po files, "\
            "for all languages, unless one or more language(s) is specified to check."

        self.parser.add_argument(
            '-l', '--language',
            type=str,
            nargs='*',
            help="Specify one or more specific language code(s) to check (eg 'ko_KR')."
        )

        self.parser.add_argument(
            '-e', '--empty',
            action='store_true',
            help="Includes empty translation strings in .prob files."
        )

    def run(self, args):
        """
        Main entry point for script
        """
        if args.verbose:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING
        logging.basicConfig(stream=sys.stdout, level=log_level)

        languages = args.language or []

        if not languages:
            root = config.LOCALE_DIR
            validate_po_files(root, args.empty)
            return

        # languages will be a list of language codes; test each language.
        for language in languages:
            root = config.LOCALE_DIR / language
            # Assert that a directory for this language code exists on the system
            if not root.isdir():
                log.error(" %s is not a valid directory.\nSkipping language '%s'", root, language)
                continue
            # If we found the language code's directory, validate the files.
            validate_po_files(root, args.empty)

main = Validate()  # pylint: disable=invalid-name

if __name__ == '__main__':
    print("Validating languages...")
    main()
    print("Finished validating languages")
