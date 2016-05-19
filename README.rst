edX i18n Tools |build-status| |coverage-status|
###############################################

Installing
==========

``python setup.py install``

Running
=======

Running commands from the edx-platform directory will default to loading the
configuration at ``./conf/locale/config.yaml``. You can specify a different
configuration file with the ``--config`` argument.

* ``i18n_tool dummy``
* ``i18n_tool extract``
* ``i18n_tool generate``
* ``i18n_tool segment``
* ``i18n_tool transifex``
* ``i18n_tool validate``


Configuration
=============

Details of the config.yaml file are in `edx-platform/conf/locale/config.yaml
<https://github.com/edx/edx-platform/blob/master/conf/locale/config.yaml>`_


Changes
=======

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

#. Install the requirements::

   $ pip install -r requirements.txt

#. Run tests::

   $ nosetests

   If you have failures because ``msgcat`` failed, you may need to install it,
   and adjust your PATH to include it.  On a Mac, for example::

   $ brew install gettext
   $ PATH=/usr/local/Cellar/gettext/0.19.3/bin/:$PATH nosetests


.. |build-status| image:: https://travis-ci.org/edx/i18n-tools.svg?branch=master
   :target: https://travis-ci.org/edx/i18n-tools
.. |coverage-status| image:: https://coveralls.io/repos/edx/i18n-tools/badge.png
   :target: https://coveralls.io/r/edx/i18n-tools
