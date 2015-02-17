import argparse
from . import config
import sys


class Runner:
    def __init__(self):
        self.args = sys.argv[1:]
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
        pass

    def run(self, args):
        raise NotImplementedError

    def __call__(self, **kwargs):
        args = self.parser.parse_known_args(self.args)[0]
        for key, val in kwargs.items():
            setattr(args, key, val)
        if args.config:
            config.CONFIGURATION = config.Configuration(args.config)
        else:
            config.CONFIGURATION = config.Configuration(config.LOCALE_DIR.joinpath('config.yaml').normpath())
        self.run(args)
