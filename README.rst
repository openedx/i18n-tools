i18n Tools |build-status| |coverage-status|
===========================================

Installing
----------

``python setup.py install``

Running
-------

Running commands from the edx-platform directory will default to loading the configuration at ``./conf/locale/config.yaml``. You can specify a different configuration file with the ``--config`` argument.

 * ``i18n_tool dummy``
 * ``i18n_tool extract``
 * ``i18n_tool generate``
 * ``i18n_tool segment``
 * ``i18n_tool transifex``
 * ``i18n_tool validate``


Configuration
-------------
Details of the config.yaml file are in `edx-platform/conf/locale/config.yaml <https://github.com/edx/edx-platform/blob/master/conf/locale/config.yaml>`_

.. |build-status| image:: https://travis-ci.org/edx/i18n-tools.svg?branch=master
   :target: https://travis-ci.org/edx/i18n-tools
.. |coverage-status| image:: https://coveralls.io/repos/edx/i18n-tools/badge.png
   :target: https://coveralls.io/r/edx/i18n-tools
