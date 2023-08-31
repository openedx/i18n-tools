#!/usr/bin/env python

"""
See https://edx-wiki.atlassian.net/wiki/display/ENG/PO+File+workflow

This task extracts all English strings from all source code
and produces three human-readable files:
   conf/locale/en/LC_MESSAGES/django-partial.po
   conf/locale/en/LC_MESSAGES/djangojs-partial.po
   conf/locale/en/LC_MESSAGES/mako.po

This task will clobber any existing django.po file.
This is because django-admin makemessages hardcodes this filename
and it cannot be overridden.

"""

from datetime import datetime
import importlib
import os
import os.path
import logging
import sys
import polib

from path import Path

from i18n import Runner
from i18n.execute import execute
from i18n.segment import segment_pofiles


EDX_MARKER = "edX translation file"
LOG = logging.getLogger(__name__)
DEVNULL = open(os.devnull, 'wb')    # pylint: disable=consider-using-with


def file_exists(path_name):
    """
    Returns True if the file exists and is not empty.
    """
    return os.path.exists(path_name) and os.path.getsize(path_name) > 0


class Extract(Runner):
    """
    Class used to extract source files
    """

    def base(self, path1, *paths):
        """Return a relative path from config.BASE_DIR to path1 / paths[0] / ... """
        root_dir = self.configuration.root_dir
        return root_dir.relpathto(path1.joinpath(*paths))

    def add_args(self):
        """
        Adds arguments
        """
        self.parser.description = __doc__

    def rename_source_file(self, src, dst):
        """
        Rename a file in the source directory.
        """
        try:
            os.rename(self.source_msgs_dir.joinpath(src), self.source_msgs_dir.joinpath(dst))
        except OSError:
            pass

    def run(self, args):
        """
        Main entry point of script
        """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        configuration = self.configuration
        configuration.locale_dir.parent.makedirs_p()
        # pylint: disable=attribute-defined-outside-init
        self.source_msgs_dir = configuration.source_messages_dir

        # The extraction process clobbers django.po and djangojs.po.
        # Save them so that it won't do that.
        self.rename_source_file('django.po', 'django-saved.po')
        self.rename_source_file('djangojs.po', 'djangojs-saved.po')

        # Extract strings from mako templates.
        verbosity_map = {
            0: "-q",
            1: "",
            2: "-v",
        }
        babel_verbosity = verbosity_map.get(args.verbose, "")

        if args.verbose:
            stderr = None
        else:
            stderr = DEVNULL

        self.babel_extract(stderr, babel_verbosity)

        makemessages = f"django-admin makemessages -l en -v{args.verbose}"
        ignores = " ".join(f'--ignore="{d}/*"' for d in configuration.ignore_dirs)
        if ignores:
            makemessages += " " + ignores

        # Extract strings from django source files (*.py, *.html, *.txt).
        make_django_cmd = makemessages + ' -d django'
        execute(make_django_cmd, working_directory=configuration.root_dir, stderr=stderr)

        # Extract strings from Javascript source files (*.js, *jsx).
        make_djangojs_cmd = makemessages + ' -d djangojs -e js,jsx'
        execute(make_djangojs_cmd, working_directory=configuration.root_dir, stderr=stderr)

        # makemessages creates 'django.po'. This filename is hardcoded.
        # Rename it to django-partial.po to enable merging into django.po later.
        self.rename_source_file('django.po', 'django-partial.po')

        # makemessages creates 'djangojs.po'. This filename is hardcoded.
        # Rename it to djangojs-partial.po to enable merging into djangojs.po later.
        self.rename_source_file('djangojs.po', 'djangojs-partial.po')

        files_to_clean = set()

        # Extract strings from third-party applications.
        for app_name in configuration.third_party:
            # Import the app to find out where it is.  Then use pybabel to extract
            # from that directory.
            app_module = importlib.import_module(app_name)
            app_dir = Path(app_module.__file__).dirname().dirname()
            output_file = self.source_msgs_dir / (app_name + ".po")
            files_to_clean.add(output_file)

            babel_cmd = 'pybabel {verbosity} extract -F {config} -c "Translators:" {app} -o {output}'
            babel_cmd = babel_cmd.format(
                verbosity=babel_verbosity,
                config=configuration.locale_dir / 'babel_third_party.cfg',
                app=app_name,
                output=output_file,
            )
            execute(babel_cmd, working_directory=app_dir, stderr=stderr)

        # Segment the generated files.
        segmented_files = segment_pofiles(configuration, configuration.source_locale)
        files_to_clean.update(segmented_files)

        # Add partial files to the list of files to clean.
        files_to_clean.update(('django_partial', 'djangojs_partial'))

        # Finish each file.
        for filename in files_to_clean:
            clean_pofile(self.source_msgs_dir.joinpath(filename))

        # Restore the saved .po files.
        self.rename_source_file('django-saved.po', 'django.po')
        self.rename_source_file('djangojs-saved.po', 'djangojs.po')

    def babel_extract(self, stderr, verbosity):
        """
        Extract strings from mako templates.
        """
        configuration = self.configuration

        # --keyword informs Babel that `interpolate()` is an expected
        # gettext function, which is necessary because the `tokenize` function
        # in the `markey` module marks it as such and passes it to Babel.
        # (These functions are called in the django-babel-underscore module.)
        babel_cmd_template = (
            'pybabel {verbosity} extract --mapping={config} '
            '--add-comments="Translators:" --keyword="interpolate" '
            '. --output={output}'
        )

        babel_mako_cfg = self.base(configuration.locale_dir, 'babel_mako.cfg')
        if babel_mako_cfg.exists():
            babel_mako_cmd = babel_cmd_template.format(
                verbosity=verbosity,
                config=babel_mako_cfg,
                output=self.base(configuration.source_messages_dir, 'mako.po'),
            )

            execute(babel_mako_cmd, working_directory=configuration.root_dir, stderr=stderr)

        babel_underscore_cfg = self.base(configuration.locale_dir, 'babel_underscore.cfg')
        if babel_underscore_cfg.exists():
            babel_underscore_cmd = babel_cmd_template.format(
                verbosity=verbosity,
                config=babel_underscore_cfg,
                output=self.base(configuration.source_messages_dir, 'underscore.po'),
            )

            execute(babel_underscore_cmd, working_directory=configuration.root_dir, stderr=stderr)


def clean_pofile(path_name):
    """
    Perform header fix, metadata fix, and key string removal on a single pofile
    """
    if not file_exists(path_name):
        return
    LOG.info('Cleaning %s', os.path.basename(path_name))
    profile = polib.pofile(path_name)
    # replace default headers with edX headers
    fix_header(profile)
    # replace default metadata with edX metadata
    fix_metadata(profile)
    # remove key strings which belong in messages.po
    strip_key_strings(profile)
    profile.save()


def fix_header(pofile):
    """
    Replace default headers with edX headers
    """

    # By default, django-admin makemessages creates this header:
    #
    #   SOME DESCRIPTIVE TITLE.
    #   Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
    #   This file is distributed under the same license as the PACKAGE package.
    #   FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.

    pofile.metadata_is_fuzzy = []   # remove [u'fuzzy']
    header = pofile.header
    fixes = (
        ('SOME DESCRIPTIVE TITLE', EDX_MARKER),
        ('Translations template for PROJECT.', EDX_MARKER),
        ('YEAR', str(datetime.utcnow().year)),
        ('ORGANIZATION', 'edX'),
        ("THE PACKAGE'S COPYRIGHT HOLDER", "EdX"),
        (
            'This file is distributed under the same license as the PROJECT project.',
            'This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.'
        ),
        (
            'This file is distributed under the same license as the PACKAGE package.',
            'This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.'
        ),
        ('FIRST AUTHOR <EMAIL@ADDRESS>', 'EdX Team <info@edx.org>'),
    )
    for src, dest in fixes:
        header = header.replace(src, dest)
    pofile.header = header


def fix_metadata(pofile):
    """
    Replace default metadata with edX metadata
    """

    # By default, django-admin makemessages creates this metadata:
    #
    #   {u'PO-Revision-Date': u'YEAR-MO-DA HO:MI+ZONE',
    #   u'Language': u'',
    #   u'Content-Transfer-Encoding': u'8bit',
    #   u'Project-Id-Version': u'PACKAGE VERSION',
    #   u'Report-Msgid-Bugs-To': u'',
    #   u'Last-Translator': u'FULL NAME <EMAIL@ADDRESS>',
    #   u'Language-Team': u'LANGUAGE <LL@li.org>',
    #   u'POT-Creation-Date': u'2013-04-25 14:14-0400',
    #   u'Content-Type': u'text/plain; charset=UTF-8',
    #   u'MIME-Version': u'1.0'}

    fixes = {
        'Report-Msgid-Bugs-To': 'openedx-translation@googlegroups.com',
        'Project-Id-Version': '0.1a',
        'Language': 'en',
        'Last-Translator': '',
        'Language-Team': 'openedx-translation <openedx-translation@googlegroups.com>',
        'Plural-Forms': 'nplurals=2; plural=(n != 1);',
    }
    pofile.metadata.pop('POT-Creation-Date', None)
    pofile.metadata.pop('PO-Revision-Date', None)
    pofile.metadata.update(fixes)


def strip_key_strings(pofile):
    """
    Removes all entries in PO which are key strings.
    These entries should appear only in messages.po, not in any other po files.
    """
    newlist = [entry for entry in pofile if not is_key_string(entry.msgid)]
    del pofile[:]
    pofile += newlist


def is_key_string(string):
    """
    returns True if string is a key string.
    Key strings begin with underscore.
    """
    return len(string) > 1 and string[0] == '_'


main = Extract()

if __name__ == '__main__':
    main()
