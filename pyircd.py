#!/usr/bin/python3

import asyncore
import argparse
import logging
import sys

from pyircd.config import Config
from pyircd.network import IRCNetwork

VERSION="dev-2"

class PyIRCD:
    """Controls the running and setup of the IRC Server"""
    def __init__(self):
        parser = argparse.ArgumentParser(description='Run the IRC Server.')
        parser.add_argument('--config', '-c', nargs='?', help='Path to the'
        ' config file', default='config.json')
        args = parser.parse_args()
        try:
            self.config = Config(args.config)
        except IOError:
            print('Invalid config file specified.')
            sys.exit(1)
        self.config.version = VERSION
        logging.basicConfig(level=logging.DEBUG)
        self.network = IRCNetwork(self.config)
        asyncore.loop()

PyIRCD()
