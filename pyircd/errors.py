class NoSuchUserError(KeyError):
    """Represents an attempt to interact with a user that does not exist."""
    def __init__(self, target):
        self.target = target


class InsufficientParamsError(Exception):
    """Represents when too few parameters were given to a command."""

    def __init__(self, command):
        self.command = command

