class NoSuchUserError(KeyError):
    """Represents an attempt to interact with a user that does not exist."""
    def __init__(self, target):
        self.target = target

class NoSuchChannelError(KeyError):
    """Represents an attempt to interact with a channel that does not
    exist."""

    def __init__(self, channel):
        self.channel = channel

class InsufficientParamsError(Exception):
    """Represents when too few parameters were given to a command."""

    def __init__(self, command):
        self.command = command

class BadKeyError(Exception):
    """Represents a failed password attempt for a room."""
    def __init__(self, channel):
        self.channel = channel

class NeedChanOpError(Exception):
    """Represent a lack of permissions for a operation."""
    def __init__(self, channel):
        self.channel = channel

class ChannelFullError(Exception):
    """Represent a failed attempt to join a full channel."""
    def __init__(self, channel):
        self.channel = channel
