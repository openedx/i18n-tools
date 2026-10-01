#!/usr/bin/env python

"""
See https://edx-wiki.atlassian.net/wiki/display/ENG/PO+File+workflow

This task merges and compiles the human-readable .po files on the
local filesystem into machine-readable .mo files. This is typically
necessary as part of the build process since these .mo files are
needed by Django when serving the web app.

The configuration file (in edx-platform/conf/locale/config.yaml) specifies which
languages to generate.

"""
import codecs
import logging
import os
import re
import sys

from path import Path as path
from polib import pofile

from i18n import Runner
from i18n.execute import execute
from i18n.extract import DJANGO_PARTIAL_PO, DJANGO_PO

LOG = logging.getLogger(__name__)
DEVNULL = open(os.devnull, "wb")        # pylint: disable=consider-using-with
DUPLICATE_ENTRY_PATTERN = re.compile('#-#-#-#-#.*#-#-#-#-#')


def merge(configuration, locale, target=DJANGO_PO, sources=(DJANGO_PARTIAL_PO,), fail_if_missing=True):
    """
    For the given locale, merge the `sources` files to become the `target`
    file.  Note that the target file might also be one of the sources.

    If fail_if_missing is true, and the files to be merged are missing,
    throw an Exception, otherwise return silently.

    If fail_if_missing is false, and the files to be merged are missing,
    just return silently.

    """
    LOG.info('Merging %s locale %s', target, locale)
    locale_directory = configuration.get_messages_dir(locale)
    valid_sources = []
    for filename in sources:
        try:
            validate_file(locale_directory, filename)
            valid_sources.append(filename)
        except (ValueError, IOError):
            if fail_if_missing:
                raise
    if not valid_sources:
        return

    # merged file is merged.po
    merge_cmd = 'msgcat -o merged.po ' + ' '.join(valid_sources)
    execute(merge_cmd, working_directory=locale_directory)

    # clean up redunancies in the metadata
    merged_filename = locale_directory.joinpath('merged.po')
    duplicate_entries = clean_pofile(merged_filename)

    # rename merged.po -> django.po (default)
    target_filename = locale_directory.joinpath(target)
    os.rename(merged_filename, target_filename)

    # Write duplicate messages to a file
    if duplicate_entries:
        dup_file = target_filename.replace(".po", ".dup")
        with codecs.open(dup_file, "w", encoding="utf8") as dfile:
            for (entry, translations) in duplicate_entries:
                dfile.write(f"{entry}\n")
                dfile.write(f"Translations found were:\n\t{translations}\n\n")
        LOG.warning(" %s duplicates in %s, details in .dup file", len(duplicate_entries), target_filename)


def merge_files(configuration, locale, fail_if_missing=True):
    """
    Merge all the files in `locale`, as specified in config.yaml.
    """
    for target, sources in configuration.generate_merge.items():
        merge(configuration, locale, target, sources, fail_if_missing)


def clean_pofile(pofile_path):
    """
    Clean various aspect of a .po file.

    Fixes:

        - Removes the fuzzy flag on metadata.

        - Removes occurrence line numbers so that the generated files don't
          generate a lot of line noise when they're committed.

    Returns a list of any duplicate entries found.
    """
    # Reading in the .po file and saving it again fixes redundancies.
    pomsgs = pofile(pofile_path)
    # The msgcat tool marks the metadata as fuzzy, but it's ok as it is.
    pomsgs.metadata_is_fuzzy = False
    duplicate_entries = []

    for entry in pomsgs:
        # Remove line numbers
        entry.occurrences = [(filename, None) for filename, __ in entry.occurrences]
        # Check for merge conflicts. Pick the first, and emit a warning.
        if 'fuzzy' in entry.flags:
            # Remove fuzzy from flags
            entry.flags = [f for f in entry.flags if f != 'fuzzy']
            # Save a warning message
            occurrences = [f for (f, __) in entry.occurrences]
            dup_msg = (f'Multiple translations found for single string.\n\t'
                       f'String "{entry.msgid}"\n\tPresent in files {occurrences}'
                       )
            duplicate_entries.append((dup_msg, entry.msgstr))

            # Pick the first entry
            for msgstr in DUPLICATE_ENTRY_PATTERN.split(entry.msgstr):
                # Ignore any empty strings that may result from the split call
                if msgstr:
                    # Set the first one we find to be the right one. Strip to remove extraneous
                    # new lines that exist.
                    entry.msgstr = msgstr.strip()

                    # Raise error if there's new lines starting or ending the id string.
                    if entry.msgid.startswith('\n') or entry.msgid.endswith('\n'):
                        raise ValueError(
                            f'{entry.msgid} starts or ends with a new line character, which is not allowed. '
                            'Please fix before continuing. Source string is found in {entry.occurrences}'
                            .encode('utf-8')
                        )
                    break

    pomsgs.save()
    return duplicate_entries


def validate_file(directory, filename):
    """
    Asserts that the given files exist.
    files_to_merge is a list of file names (no directories).
    directory is the directory (a path object from path.py) in which the files should appear.
    raises an Exception if any of the files are not in dir.
    """
    pathname = directory.joinpath(filename)
    if not pathname.exists():
        raise ValueError(f"I18N: Cannot generate because file not found: {pathname}")
    # clean sources
    clean_pofile(pathname)


class Generate(Runner):
    """Generate merged and compiled message files."""

    def add_args(self):
        self.parser.description = "Generate merged and compiled message files."
        self.parser.add_argument("--strict", action='store_true', help="Complain about missing files.")
        self.parser.add_argument("--ltr", action='store_true', help="Only generate for LTR languages.")
        self.parser.add_argument("--rtl", action='store_true', help="Only generate for RTL languages.")

    def run(self, args):
        """
        Main entry point for script
        """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

        configuration = self.configuration
        if args.ltr:
            langs = configuration.ltr_langs
        elif args.rtl:
            langs = configuration.rtl_langs
        else:
            langs = configuration.translated_locales

        for locale in langs:
            merge_files(configuration, locale, fail_if_missing=args.strict)
        # Dummy text is not required. Don't raise exception if files are missing.
        for locale in configuration.dummy_locales:
            merge_files(configuration, locale, fail_if_missing=False)
        # Merge the source locale, so we have the canonical .po files.
        if configuration.source_locale not in langs:
            merge_files(configuration, configuration.source_locale, fail_if_missing=args.strict)

        compile_cmd = f'django-admin compilemessages -v{args.verbose}'
        if args.verbose:
            stderr = None
        else:
            stderr = DEVNULL
        execute(compile_cmd, working_directory=configuration.root_dir, stderr=stderr)

        # Check for any mapped languages and copy directories around accordingly
        for source_locale, dest_locale in configuration.edx_lang_map.items():
            source_dirname = configuration.get_messages_dir(source_locale)
            dest_dirname = configuration.get_messages_dir(dest_locale)
            LOG.info("Copying mapped locale %s to %s", source_dirname, dest_dirname)

            path.rmtree_p(path(dest_dirname))
            path.copytree(path(source_dirname), path(dest_dirname))


main = Generate()

if __name__ == '__main__':
    main()
