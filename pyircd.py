#!/usr/bin/python3

import asyncore

from pyircd.config import Config
from pyircd.net import IRCNet

VERSION="dev-2"

class PyIRCD:
    """Controls the running and setup of the IRC Server"""
    def __init__(self):
        self.config = Config()
        self.config.version = VERSION
        self.network = IRCNet(self.config)
        asyncore.loop()

PyIRCD()
