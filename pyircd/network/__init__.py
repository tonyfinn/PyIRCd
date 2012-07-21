import logging

from .server import IRCServer
from .remote_server import RemoteServer
from ..errors import NoSuchUserError
from ..channel import NoSuchChannelError
from ..message import Message


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

    def add_server(self, sname, hopcount, token, spw, con):
        """Adds a server to the network.

        The config is checked and if there is a server in the config that
        matches the sname and spw parameter, the server is added.

        sname should be the name the server refers to itself as. hopcount is
        the amount of connections that the server goes through to get to this
        server. If the server is directly connected to this server, hopcount
        should be 1. The token is the identifier for which server behind that
        connection this server is. It is unique per connection, but not unique
        over all connections.

        """
        logging.info("Links are: %s", self.config.allowed_links)
        for link in self.config.allowed_links:
            if link['name'] == sname and link['pw'] == spw:
                logging.info("Adding server %s", sname)
                server = RemoteServer(sname, hopcount, token, self, con)
                self.servers[sname] = server
                server.send_msg(Message('PASS', [link['mypw']], False, self))
                server.send_msg(
                    Message(
                        'SERVER',
                        [self.config.hostname, '0', token], False, self))

                self.send_initial_to_server(server)
            else:
                logging.info("%s, %s do not match %s, %s",
                    link['name'], link['pw'], sname, spw)

    def quit_local_user(self, user, reason=None):
        """Handle a local user quitting appropriately."""
        self.local_server.quit_user(user, reason)
        self.quit_user(user, reason)

    def quit_user(self, user, reason=None):
        """Handle a user quitting the network."""
        logging.info("User quitting: %s", user.nick)
        for channel in self.channels.values():
            if user in channel:
                channel.part(user, reason)

    def send_initial_to_server(self, server):
        """Send all the information required for a new server's connection.

        This include SERVER messages for all other servers this server knows
        about, NICK messages for all users this server knows about, and NJOIN
        messages for all public channels this server knows about.

        """
        logging.info("Sending new server info on: %s:",
                [self.local_server.users])
        for id_, user in self.local_server.users.items():
            params = [user.nick, str(user.hopcount), user.username, user.host,
                    str(1), # TODO dummy value
                    '+' + ''.join(user.modes), user.real_name]
            message = Message('NICK', params, True, self.local_server)
            server.send_msg(message)

        for name, channel in self.channels.items():
            channel.send_njoin_info(server)
        
    def get_channel(self, channel):
        """Get a channel object for a given channel name.

        This should only be called when looking for #channels only. In
        general, server.get_channel should be called instead, which will try
        to locate a channel in the correct place for different types of
        channel. This method will be called by server.get_channel for
        #channels.

        Raises a NoSuchChannelError if there is no network wide channel of
        that name.

        """
        if channel[0] != '#':
            logging.warn('Network.get_channel called with non-#channel %s',
                channel)
        try:
            return self.channels[channel]
        except KeyError:
            raise NoSuchChannelError(channel)

    def add_user(self, user):
        self.used_nicks.append(user.nick)

    @property
    def source_str(self):
        return self.local_server.source_str
    
