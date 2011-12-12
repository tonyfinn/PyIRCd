from .server import IRCServer

class NoSuchUserError(Exception):
    pass
    

class IRCNetwork:
    """Handle the entire network of IRC objects.

    Usually, this will either delegate to the local server or send on commands
    to remote servers.

    """
    def __init__(self, config):
        self.config = config
        self.local_server = IRCServer(config, self)
        self.servers = {}
        self.channels = {}
        self.used_nicks = []

    def get_user(self, nick):
        """Get a user object for a nickname.

        Raises a NoSuchUserError if the user is not connected to the network.

        """
        servers = [self.local_server] + list(self.servers.values())
        for server in servers:
            try:
                user = server.get_user(nick)
                return user
            except NoSuchUserError:
                pass # Try next server
        raise NoSuchUserError(nick)

    def add_server(self, server):
        pass

    def add_user(self, user):
        self.used_nicks.append(user.nick)
