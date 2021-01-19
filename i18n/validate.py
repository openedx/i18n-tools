"""Tests that validate .po files."""


import codecs
import logging
import os
import struct
import sys
import textwrap

import polib

from i18n.dummy import is_format_message
from i18n.execute import call
from i18n.converter import Converter
from i18n import Runner

log = logging.getLogger(__name__)


def validate_po_files(configuration, locale_dir, root_dir=None, report_empty=False, check_all=False):
    """
    Validate all of the po files found in the root directory that are not product of a merge.

    Returns a boolean indicating whether or not problems were found.
    """
    found_problems = False

    # List of .po files that are the product of a merge (see generate.py).
    merged_files = configuration.generate_merge.keys()

    for dirpath, __, filenames in os.walk(root_dir if root_dir else locale_dir):
        for name in filenames:
            __, ext = os.path.splitext(name)
            filename = os.path.join(dirpath, name)

            # Validate only .po files that are not product of a merge (see generate.py) unless check_all is true.
            # If django-partial.po has a problem, then django.po will also, so don't report it.
            if ext.lower() == '.po' and (check_all or os.path.basename(filename) not in merged_files):

                # First validate the format of this file
                if msgfmt_check_po_file(locale_dir, filename):
                    found_problems = True

                # Check that the translated strings are valid, and optionally
                # check for empty translations. But don't check English.
                if "/locale/en/" not in filename:
                    problems = check_messages(filename, report_empty)
                    if problems:
                        report_problems(filename, problems)
                        found_problems = True

                    dup_filename = filename.replace('.po', '.dup')
                    has_duplicates = os.path.exists(dup_filename)
                    if has_duplicates:
                        log.warning("Duplicates found in %s, details in .dup file", dup_filename)
                        found_problems = True

                    if not (problems or has_duplicates):
                        log.info("No problems found in %s", filename)

    return found_problems


def msgfmt_check_po_file(locale_dir, filename):
    """
    Call GNU msgfmt -c on each .po file to validate its format.
    Any errors caught by msgfmt are logged to log.

    Returns a boolean indicating whether or not problems were found.
    """
    found_problems = False

    # Use relative paths to make output less noisy.
    rfile = os.path.relpath(filename, locale_dir)
    out, err = call(f'msgfmt -c -o /dev/null {rfile}', working_directory=locale_dir)
    if err:
        log.info('\n{}'.format(out.decode('utf8')))
        log.warning('\n{}'.format(err.decode('utf8')))
        found_problems = True

    return found_problems


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
    return {t for t in tags if not is_linguistic_tag(t)}


def astral(msg):
    """Does `msg` have characters outside the Basic Multilingual Plane?"""
    # Python2 narrow builds present astral characters as surrogate pairs.
    # By encoding as utf32, and decoding DWORDS, we can get at the real code
    # points.
    utf32 = msg.encode("utf32")[4:]         # [4:] to drop the bom
    code_points = struct.unpack("%dI" % (len(utf32) / 4), utf32)
    return any(cp > 0xFFFF for cp in code_points)


def check_messages(filename, report_empty=False):
    """
    Checks messages in `filename` in various ways:

    * Translations must have the same slots as the English.

    * Messages can't have astral characters in them.

    If `report_empty` is True, will also report empty translation strings.

    Returns the problems, a list of tuples. Each is a description, a msgid, and
    then zero or more translations.

    """
    problems = []
    pomsgs = polib.pofile(filename)
    for msg in pomsgs:
        # Check for characters Javascript can't support.
        # https://code.djangoproject.com/ticket/21725
        if astral(msg.msgstr):
            problems.append(("Non-BMP char", msg.msgid, msg.msgstr))

        if is_format_message(msg):
            # LONG_DATE_FORMAT, etc, have %s etc in them, and that's ok.
            continue

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
                id_has = ", ".join(sorted(f'"{t}"' for t in id_tags - tx_tags))
                tx_has = ", ".join(sorted(f'"{t}"' for t in tx_tags - id_tags))
                if id_has and tx_has:
                    diff = f"{id_has} vs {tx_has}"
                elif id_has:
                    diff = f"{id_has} missing"
                else:
                    diff = f"{tx_has} added"
                problems.append((
                    "Different tags in source and translation",
                    source,
                    translation,
                    diff
                ))

    return problems


def report_problems(filename, problems):
    """
    Report on the problems found in `filename`.

    `problems` is a list of tuples as returned by `check_messages`.

    """
    problem_file = filename.replace(".po", ".prob")
    id_filler = textwrap.TextWrapper(width=79, initial_indent="  msgid: ", subsequent_indent=" " * 9)
    tx_filler = textwrap.TextWrapper(width=79, initial_indent="  -----> ", subsequent_indent=" " * 9)
    with codecs.open(problem_file, "w", encoding="utf8") as prob_file:
        for problem in problems:
            desc, msgid = problem[:2]
            prob_file.write("{}\n{}\n".format(desc, id_filler.fill(msgid)))
            info = "{}\n{}\n".format(desc, id_filler.fill(msgid))
            for translation in problem[2:]:
                prob_file.write("{}\n".format(tx_filler.fill(translation)))
                info += "{}\n".format(tx_filler.fill(translation))
            log.info(info)
            prob_file.write("\n")

    log.error("%s problems in %s, details in .prob file", len(problems), filename)


class Validate(Runner):
    """
    The `validate` command for checking that .po files have no errors.
    """

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

        self.parser.add_argument(
            '-ca', '--check-all',
            action='store_true',
            help="Validate all po files, including those that are the product of a merge (see generate.py)."
        )

    def run(self, args):
        """
        Main entry point for script

        Returns an integer representing the exit code that should be returned by the script.
        """
        command_exit_code = 0

        if args.verbose:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING
        logging.basicConfig(stream=sys.stdout, level=log_level)

        languages = args.language or []
        locale_dir = self.configuration.locale_dir

        if not languages:
            # validate all languages
            if validate_po_files(self.configuration, locale_dir, report_empty=args.empty, check_all=args.check_all):
                command_exit_code = 1
        else:
            # languages will be a list of language codes; test each language.
            for language in languages:
                root_dir = self.configuration.locale_dir / language
                # Assert that a directory for this language code exists on the system
                if not root_dir.isdir():
                    log.error("%s is not a valid directory.\nSkipping language '%s'", root_dir, language)
                    continue
                # If we found the language code's directory, validate the files.
                if validate_po_files(self.configuration, locale_dir, root_dir=root_dir, report_empty=args.empty,
                                     check_all=args.check_all):
                    command_exit_code = 1

        return command_exit_code


main = Validate()

if __name__ == '__main__':
    print("Validating languages...")
    exit_code = main()
    print("Finished validating languages")
    sys.exit(exit_code)
