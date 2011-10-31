import asyncore
import socket
from pyircd.con import IRCCon
from pyircd.channel import Channel
from pyircd.ircutils import *
from pyircd import numerics

class IRCNet(asyncore.dispatcher):
    """Handles the network aspect of the IRC server."""

    def __init__(self, config, handler_class=IRCCon):
        asyncore.dispatcher.__init__(self)
        self.config = config
        self.handler_class = handler_class

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((self.config.hostname, self.config.port))
        self.listen(5)
        
        self.users = {}
        self.channels = {}

        self.used_nicks = []

    def handle_accepted(self, conn, address):
        """Handle a new connection to the server."""
        self.handler_class(conn, address, self)

    def connect_user(self, user):
        """Add a user to the server"""
        self.users[user.hostmask] = user
        self.used_nicks.append(user.nick)

    def quit_user(self, user, reason=None):
        """Remove a user from the server"""
        if user in self.users:
            del self.users[user.hostmask]
            used_nicks.remove(user.nick)
        for channel in list(self.channels.keys()):
            if user in self.channels[channel]:
                if reason:
                    self.channels[channel].part(user, reason)
                else:
                    self.channels[channel].part(user)

    def remove_channel(self, channel):
        """Remove a channel from the server."""
        if channel.name in self.channels:
            del self.channels[channel.name]

    def join_user_to_channel(self, user, channel):
        """Add a user to a channel, creating it if it does not exist. """
        if channel in self.channels:
            self.channels[channel].join(user)
        elif is_channel_name(channel):
            self.channels[channel] = Channel(channel, self)
            self.channels[channel].join(user)
            self.channels[channel].add_mode_to_user('o', user)

        user.channels.append(self.channels[channel])

        self.channels[channel].send_topic(user)
        self.channels[channel].send_user_list(user)

    def get_channel(self, channel):
        """Get the channel object given a channel name.
        
        Raises a KeyError if there is no such channel with that name.
        """
        return self.channels[channel]

    def get_user(self, nick):
        """Get the user object for a nickname.
        
        Raises a KeyError if the user is not connected to the server.
        """
        for user in self.users.values():
            if user.nick == nick:
                return user

        raise KeyError

    def send_isupport(self, user):
        """Send the ISUPPORT details to the user."""
        user.send_numeric(
            numerics.RPL_ISUPPORT,
            [
                self.config.netname
            ]
        )

    def send_motd(self, user):
        """Send the MOTD to the user."""
        user.send_numeric(numerics.RPL_MOTDSTART, [self.config.hostname])
        for line in self.config.motd.splitlines():
            user.send_numeric(numerics.RPL_MOTD, [line])
        user.send_numeric(numerics.RPL_ENDOFMOTD, [])

    def send_whois(self, whois_target, reply_user):
        """Send a user WHOIS details on another user."""
        try:
            tuser = self.get_user(whois_target)
            self.send_whois_data(tuser, reply_user)
        except KeyError:
            reply_user.send_numeric(
                numerics.ERR_NOSUCHNICK,
                [
                    whois_target
                ]
            )
    
    def send_whois_data(self, whois_target, reply_user):
        """Send the reply to a WHOIS message."""
        reply_user.send_numeric(
            numerics.RPL_WHOISUSER,
            [
                whois_target.nick,
                whois_target.username,
                whois_target.host,
                whois_target.real_name
            ]
        )

        reply_user.send_numeric(
            numerics.RPL_WHOISSERVER,
            [
                whois_target.nick,
                self.config.netname,
                self.config.info
            ]
        )

        reply_user.send_numeric(
            numerics.RPL_WHOISIDLE,
            [whois_target.nick, 0] #TODO handle idle times
        )

        reply_user.send_numeric(
            numerics.RPL_WHOISCHANNELS,
            [
                whois_target.nick,
                ' '.join(
                    [channel.name for channel in whois_target.channels]
                )
            ]
        )

        reply_user.send_numeric(
            numerics.RPL_ENDOFWHOIS,
            [whois_target.nick]
        )
