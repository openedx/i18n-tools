edX i18n Tools |build-status| |coverage-status|
###############################################

Installing
==========

EdX i18n tools are a set of commands useful for developers and translators to
extract, compile and validate translations. The edX i18n tools can be installed
running the following command inside the extracted directory.

``python setup.py install``

Running
=======

For Django projects, commands should be run from the root directory, and
the default configuration will be found at ``./conf/locale/config.yaml``.
For Django apps, commands should be run from the app's directory, and
the default configuration will be found at ``./locale/config.yaml``.

You can specify a different configuration file with the ``--config`` argument.


General Commands
================

* To extract source strings and populate ``.po`` translation files with them

  * ``i18n_tool extract``

* To generate test language(eo) translation files from source ``.po`` files

  * ``i18n_tool dummy``

* To compile ``.po`` translation files into ``.mo`` message files

  * ``i18n_tool generate``

* To find translation errors in ``.po`` files

  * ``i18n_tool validate``

* To determine if the source translation files(``.po``) are up-to-date

  * ``i18n_tool changed``

* To segment a ``.po`` file into smaller files based on the locations of the messages

  * ``i18n_tool segment``


Transifex Commands
==================

Developers or translators can use commands provided by edX i18n tools to upload
translations to Transifex or download them. Before using these commands one
should have an account on `transifex.com <https://www.transifex.com/>`_ to
create a ``~/.transifexrc`` file.  Once the Transifex account has been set up,
create a ``~/.transifexrc`` file having these contents::

   [https://www.transifex.com]
   hostname = https://www.transifex.com
   password = YOURPASSWORD
   token =
   username = YOURUSERNAME(EMAIL)


Also make sure you have a Transifex configuration file ``.tx/config`` present
under the project directory.

* To upload translations to Transifex

  * ``i18n_tool transifex push``

* To download translations from Transifex

  * ``i18n_tool transifex pull``

Configuration
=============

Details of the config.yaml file are in `edx-platform/conf/locale/config.yaml
<https://github.com/openedx/edx-platform/blob/master/conf/locale/config.yaml>`_


Changes
=======
v0.5.0
-------

* Added Django22 support.

v0.4.9
-------

* Updated validate to log problems found in translations.

v0.4.8
-------

* Updated transifex to pull files from Transifex that are atleast 3% done
  previous value was 10%.

v0.4.7
-------

* Test that tag validation catches HTML added to translations.

* When tag validation finds differences, output should be deterministic.

v0.4.6
-------

* Ensure that we only pull files from Transifex that are 10% done.
  Avoids a problem with our validation code choking on empty po files
  and avoids translations that are just getting started.

* Don't complain about obviously missing files when cleaning
  the headers of just-pulled files, and make sure that we do
  notice the files we did actually pull.

* Ensure that Plural-Forms has a valid value when extracting.
  python-gettext will choke otherwise.

* When creating a dummy po file, don't garble source strings in
  a way that relies on the Python dictionary order. This way the
  result will always be the same no matter the machine.

v0.4.5
-------

* Extract from .jsx files too.

v0.4.4
-------

* Added check-all (check all po files) argument to validate command.

v0.4.3
-------

* Specify Language header for generated dummy po files.

v0.4.2
-------

* Specified utf-8 encoding for .yaml file.

v0.4.1
-------

* Fixes bug preventing the use of --empty with The validate command.

v0.4.0
-------

* The validate command returns a non-zero exit code when problems are detected with the translation files.

v0.3.10
-------

* Add support for edx_lang_map in config.yaml to share translations across language codes.

v0.3.9
------

* Fix Python 3 issues in validate.

v0.3.8
------

* Added support for Django 1.11 and Python 3.6

v0.3.7
------

* A few small fixes for Django projects.

v0.3.6
------

* Major refactoring to enable use on Django apps as well as Django projects.

v0.3.5
------

* Pinned a requirement to prevent failures when used with other applications.

v0.3.4
------

* ``i18n_tool changed`` command added. This command determines if the source
  translation files are up-to-date. If they are not it returns a non-zero exit
  code.

v0.3.2
------

* ``i18n_tool validate`` no longer complains about problems in both the
  component .po files and the combined .po files.

v0.3.1
------

* ``i18n_tool extract`` will preserve existing django.po and djangojs.po files
  in the source directory.

v0.3
----

* ``i18n_tool transifex push`` and ``i18n_tool transifex pull`` now can take
  optional resource names on the command line.  If not provided, all resources
  are pushed/pulled.

v0.2.1
------

* ``i18n_tool validate`` no longer leaves an unneeded messages.mo file behind.


Development
===========

To work on this code:

#. Install Tox::

   $ pip install tox

#. Run tests::

   $ tox

   If you have failures because ``msgcat`` failed, you may need to install it,
   and adjust your PATH to include it.  On a Mac, for example::

   $ brew install gettext
   $ PATH=/usr/local/Cellar/gettext/0.19.3/bin/:$PATH tox


.. |build-status| image:: https://travis-ci.com/edx/i18n-tools.svg?branch=master
   :target: https://travis-ci.com/edx/i18n-tools
.. |coverage-status| image:: https://coveralls.io/repos/edx/i18n-tools/badge.png
   :target: https://coveralls.io/r/edx/i18n-tools
