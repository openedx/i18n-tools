"""
Utility library file for executing shell commands
"""
import os
import subprocess as sp
import logging

from i18n import config

LOG = logging.getLogger(__name__)


def execute(command, working_directory=config.BASE_DIR, stderr=sp.STDOUT):
    """
    Executes shell command in a given working_directory.
    Command is a string to pass to the shell.
    Output is ignored.
    """
    LOG.info(u"Executing in %s ...", working_directory)
    LOG.info(command)
    sp.check_call(command, cwd=working_directory, stderr=stderr, shell=True)


def call(command, working_directory=config.BASE_DIR):
    """
    Executes shell command in a given working_directory.
    Command is a list of strings to execute as a command line.
    Returns a tuple of two byte strings: (stdout, stderr)

    """
    LOG.info(command)
    proc = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, cwd=working_directory, shell=True)
    out, err = proc.communicate()
    return (out, err)


def remove_file(filename, verbose=True):
    """
    Attempt to delete filename.
    log is boolean. If true, removal is logged.
    Log a warning if file does not exist.
    Logging filenames are relative to config.BASE_DIR to cut down on noise in output.
    """
    if verbose:
        LOG.info(u'Deleting file %s', os.path.relpath(filename, config.BASE_DIR))
    if not os.path.exists(filename):
        LOG.warning(u"File does not exist: %s", os.path.relpath(filename, config.BASE_DIR))
    else:
        os.remove(filename)
