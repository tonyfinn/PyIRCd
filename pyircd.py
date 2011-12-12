#!/usr/bin/python3

import asyncore
import logging

from pyircd.config import Config
from pyircd.network import IRCNetwork

VERSION="dev-2"

class PyIRCD:
    """Controls the running and setup of the IRC Server"""
    def __init__(self):
        self.config = Config()
        self.config.version = VERSION
        logging.basicConfig(level=logging.DEBUG)
        self.network = IRCNetwork(self.config)
        asyncore.loop()

PyIRCD()
