"""
Tool to be used by other IDAs for internationalization.
"""
import argparse
import sys

from . import config

__version__ = '0.4.1'


class Runner:
    """
    Runner class for internationalization.
    """
    def __init__(self):
        self.args = sys.argv[1:]
        self.configuration = None
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '--config',
            '-c',
            help='configuration file'
        )
        self.parser.add_argument(
            '-v', '--verbose',
            action='count', default=0,
            help="Turns on info-level logging."
        )
        self.add_args()

    def add_args(self):
        """
        Add arguments
        """
        pass

    def run(self, args):
        """
        Runs the runner with the given args.
        :param args: Arguments for the runner
        """
        raise NotImplementedError

    def __call__(self, **kwargs):
        args = self.parser.parse_known_args(self.args)[0]
        for key, val in kwargs.items():
            setattr(args, key, val)
        root_dir = kwargs.get('root_dir')
        self.configuration = config.Configuration(filename=args.config, root_dir=root_dir)
        return self.run(args)
