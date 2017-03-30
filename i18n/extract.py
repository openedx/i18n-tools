#!/usr/bin/env python

"""
This task extracts English strings from source code using the configured extractors. Extractors should be configured in
conf/locale/config.yaml. Supported extractors include:
    - django
        - extracts strings from django project files (both python and js)
        - produces two files:
             - conf/locale/en/LC_MESSAGES/django-partial.po
             - conf/locale/en/LC_MESSAGES/djangojs-partial.po
        - may specify optional list of directories to ignore for extraction by setting 'ignore_dirs' option
    - javascript
        - extracts strings from javascript files
        - produces: conf/locale/en/LC_MESSAGES/javascript.po
        - must have babel_javascript.cfg file in conf/locale/ directory
        - may specify optional list of keywords (names of functions used to mark strings for translation) by setting
            'keywords' option.
    - underscore
        - extracts strings from underscore templates
        - produces: conf/locale/en/LC_MESSAGES/underscore.po
        - must have babel_underscore.cfg file in conf/locale/ directory
        - may specify optional list of keywords (names of functions used to mark strings for translation) by setting
            'keywords' option.
    - mako
        - extracts strings from mako templates
        - produces: conf/locale/en/LC_MESSAGES/mako.po
        - must have babel_mako.cfg file in conf/locale/ directory
        - may specify optional list of keywords (names of functions used to mark strings for translation) by setting
            'keywords' option.
    - third_party:
        - extracts strings from third party libraries
        - produces one file for each library: conf/locale/en/LC_MESSAGES/<library_name>.po
        - must have babel_third_party.cfg file in conf/locale/ directory
        - must specify list of third_party libraries from which strings should be extracted via the 'applications'
            option.
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
DEVNULL = open(os.devnull, 'wb')


class Extract(Runner):
    """
    Class used to extract source files
    """

    def base(self, path1, *paths):
        """Return a relative path from config.BASE_DIR to path1 / paths[0] / ... """
        root_dir = self.configuration.root_dir
        return root_dir.relpathto(path1.joinpath(*paths))  # pylint: disable=no-value-for-parameter

    def add_args(self):
        """
        Adds arguments
        """
        self.parser.description = __doc__  # pylint: disable=invalid-name

    def rename_source_file(self, src, dst):
        """
        Rename a file in the source directory.
        """
        os.rename(self.source_msgs_dir.joinpath(src), self.source_msgs_dir.joinpath(dst))

    def run(self, args):
        """
        Main entry point of script
        """
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        configuration = self.configuration
        configuration.locale_dir.parent.makedirs_p()
        configuration.source_messages_dir.makedirs_p()
        self.source_msgs_dir = configuration.source_messages_dir  # pylint: disable=attribute-defined-outside-init

        verbosity_map = {0: "-q", 1: "", 2: "-v"}
        babel_verbosity = verbosity_map.get(args.verbose, "")
        stderr = None if args.verbose else DEVNULL
        babel_extractors = {'javascript', 'mako', 'underscore'}

        files_created = set()
        for extractor, extractor_opts in configuration.extractors.items():
            if extractor == 'django':
                files_created.update(
                    self.extract_django(
                        working_dir=configuration.root_dir,
                        verbosity=args.verbose,
                        stderr=stderr,
                        options=extractor_opts
                    )
                )

            elif extractor in babel_extractors:
                output_filename = '{extractor}.po'.format(extractor=extractor)
                babel_config_filename = 'babel_{extractor}.cfg'.format(extractor=extractor)

                self.extract_babel(
                    working_dir=configuration.root_dir,
                    babel_config=self.base(configuration.locale_dir, babel_config_filename),
                    input_dir='.',
                    output_file=self.base(configuration.source_messages_dir, output_filename),
                    verbosity=babel_verbosity,
                    stderr=stderr,
                    options=extractor_opts
                )
                files_created.add(output_filename)

            elif extractor == 'third_party':
                files_created.update(
                    self.extract_third_party(
                        babel_config=self.base(configuration.locale_dir, 'babel_third_party.cfg'),
                        output_dir=configuration.source_messages_dir,
                        verbosity=babel_verbosity,
                        stderr=stderr,
                        options=extractor_opts
                    )
                )

            else:
                raise RuntimeError('Extractor ({}) is not supported'.format(extractor))

        # Finish each file.
        self.clean_files(files_created)

        # Segment the generated files.
        segment_pofiles(configuration, "en")

    def extract_django(self, working_dir, verbosity, stderr, options=None):
        """ Extract translation strings from files in a django project. """

        # The extraction process clobbers django.po and djangojs.po.
        # Save them so that it won't do that.
        self.rename_source_file('django.po', 'django-saved.po')
        self.rename_source_file('djangojs.po', 'djangojs-saved.po')

        # Build the command.
        makemessages = "django-admin.py makemessages -l en -v{verbosity}".format(verbosity=verbosity)
        if options and options.get('ignore_dirs'):
            makemessages += ' ' + ' '.join('--ignore="{}/*"'.format(d) for d in options['ignore_dirs'])

        # Extract strings from django source files (*.py, *.html, *.txt).
        make_django_cmd = makemessages + ' -d django'
        execute(make_django_cmd, working_directory=working_dir, stderr=stderr)

        # Extract strings from Javascript source files (*.js).
        make_djangojs_cmd = makemessages + ' -d djangojs'
        execute(make_djangojs_cmd, working_directory=working_dir, stderr=stderr)

        # makemessages creates 'django.po' and djangojs.po. These filenames are hardcoded.
        # Rename them so that they may be merged into the final django.po/djangojs.po files later.
        self.rename_source_file('django.po', 'django-partial.po')
        self.rename_source_file('djangojs.po', 'djangojs-partial.po')

        # Restore the saved .po files.
        self.rename_source_file('django-saved.po', 'django.po')
        self.rename_source_file('djangojs-saved.po', 'djangojs.po')

        # Return the names of the files that were created.
        return {'django-partial.po', 'djangojs-partial.po'}

    def extract_babel(self, working_dir, babel_config, input_dir, output_file, verbosity, stderr, options=None):
        """ Extract translation strings from source code using babel. """

        if not babel_config.exists():
            raise RuntimeError('Could not find babel config file ({file}).'.format(file=babel_config))

        # Buld the command
        command = 'pybabel {verbosity} extract --mapping={config} --add-comments="Translators:"'.format(
            verbosity=verbosity,
            config=babel_config
        )

        # If optional keywords (names of functions used to mark strings for translation) were configured, add them
        # to the command
        if options and options.get('keywords'):
            command += ' --keywords="{keywords}"'.format(keywords=' '.join([key for key in options['keywords']]))

        # Add the input_dir and output_file to the command
        command += ' {input_dir} --output={output_file}'.format(input_dir=input_dir, output_file=output_file)

        # Run the command
        execute(command, working_directory=working_dir, stderr=stderr)

    def extract_third_party(self, babel_config, output_dir, verbosity, stderr, options):
        """ Extract translation strings from third party libraries using babel. """

        files_created = set()

        for app_name in options['applications']:
            # Import the app to find out where it is. Then use pybabel to extract from that directory.
            app_module = importlib.import_module(app_name)
            app_dir = Path(app_module.__file__).dirname().dirname()  # pylint: disable=no-value-for-parameter

            output_filename = '{app_name}.po'.format(app_name=app_name)
            output_file = self.base(output_dir, output_filename)

            self.extract_babel(
                working_dir=app_dir,
                babel_config=babel_config,
                input_dir=app_name,
                output_file=output_file,
                verbosity=verbosity,
                stderr=stderr
            )

            files_created.add(output_filename)

        # Return the names of the files that were created
        return files_created

    def clean_files(self, files):
        """ Clean up the files so that they're formatted consistently. """

        for filename in files:
            LOG.info('Cleaning %s', filename)
            pofile = polib.pofile(self.source_msgs_dir.joinpath(filename))
            # replace default headers with edX headers
            fix_header(pofile)
            # replace default metadata with edX metadata
            fix_metadata(pofile)
            # remove key strings which belong in messages.po
            strip_key_strings(pofile)
            pofile.save()


def fix_header(pofile):
    """
    Replace default headers with edX headers
    """

    # By default, django-admin.py makemessages creates this header:
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

    # By default, django-admin.py makemessages creates this metadata:
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
        'PO-Revision-Date': datetime.utcnow(),
        'Report-Msgid-Bugs-To': 'openedx-translation@googlegroups.com',
        'Project-Id-Version': '0.1a',
        'Language': 'en',
        'Last-Translator': '',
        'Language-Team': 'openedx-translation <openedx-translation@googlegroups.com>',
    }
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

main = Extract()  # pylint: disable=invalid-name

if __name__ == '__main__':
    main()
