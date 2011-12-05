import asyncore
import socket
from pyircd.con import IRCCon
from pyircd.channel import Channel
from pyircd.message import Message
from pyircd.errors import NoSuchUserError, NoSuchChannelError, \
InsufficientParamsError
from pyircd.ircutils import *
from pyircd import numerics

class InvalidChannelError(Exception): pass

# Don't test this class as it's all about IO.
class NetworkHandler(asyncore.dispatcher): # pragma: no cover
    def __init__(self, server, handler_class=IRCCon):
        asyncore.dispatcher.__init__(self)
        self.server = server
        self.handler_class = handler_class
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((self.server.config.hostname, self.server.config.port))
        self.listen(5)

    def handle_accepted(self, conn, address):
        con = self.handler_class(conn, address, self.server)
        self.server.handle_new_connection(con)

    def handle_close(self):
        self.close()

class IRCNet:
    """Handles the network aspect of the IRC server."""

    def __init__(self, config, handler_class=IRCCon,
            netaccess_class=NetworkHandler):
        self.config = config
        self.netaccess = netaccess_class(self)
        self.handler_class = handler_class

        self.highest_unique_id = 0

        self.users = {}
        self.channels = {}

        self.used_nicks = []

    def handle_new_connection(self, con):
        """Handle a new connection to the server."""
        # The class is using the highest unique id to set it's own id.
        # Make sure it's always incremented after creating a new instnace.
        self.highest_unique_id += 1

    def connect_user(self, user):
        """Add a user to the server"""
        self.users[user.unique_id] = user
        self.used_nicks.append(user.nick)

    def quit_user(self, user, reason=None):
        """Remove a user from the server.
        
        If the user is connected to any channels, the user will be parted 
        from each channel. If a quit message is specified, it is used as the
        part reason.
        
        """
        if user.unique_id in self.users:
            del self.users[user.unique_id]
            self.used_nicks.remove(user.nick)
        for channel in list(self.channels.keys()):
            if user in self.channels[channel]:
                if reason:
                    self.channels[channel].part(user, reason)
                else:
                    self.channels[channel].part(user)

    def remove_channel(self, channel):
        """Remove a channel from the server.
        
        This should only be called if the channel has no members. It does not
        notify members about the removal of the channel.
        
        """
        if channel.name in self.channels:
            del self.channels[channel.name]

    def join_user_to_channel(self, user, channel, key=None):
        """Add a user to a channel.
        
        If the channel does not exist, it will be created and added to the
        server. The user will be made an op of the newly created channel.
        If the channel does exist and has a key which does not match
        that provided in the key parameter, a BadKeyError is raised. If a
        limit is set on that channel, and the number of users is equal to or
        greater than the limit, then a ChannelFullError is raised.
        
        """
        if channel in self.channels:
            self.channels[channel].join(user, key)
        elif is_channel_name(channel):
            self.channels[channel] = Channel(channel, self)
            self.channels[channel].join(user, key)
            self.channels[channel].add_mode_to_user('o', user, 
                source=self.config.hostname)
        else:
            raise InvalidChannelError("Invalid Channel Name")

        self.channels[channel].send_topic(user)
        self.channels[channel].send_user_list(user)

    def get_channel(self, channel):
        """Get the channel object given a channel name.
        
        Raises a NoSuchChannelError if there is no such channel with that name.

        """
        try:
            return self.channels[channel]
        except KeyError:
            raise NoSuchChannelError(channel)

    def get_user(self, nick):
        """Get the user object for a nickname.
        
        Raises a NoSuchUserError if the user is not connected to the server.

        """
        for user in self.users.values():
            if user.nick == nick:
                return user

        raise NoSuchUserError(nick)

    def send_isupport(self, user):
        """Send the ISUPPORT details to the user."""
        user.send_numeric(
            numerics.RPL_ISUPPORT,
            [
                self.config.netname
            ]
        )

    def try_make_oper(self, user, opname, pw):
        """Attempt to make a user an oper with the given name and password.

        These are compared to the oper passwords that are stored in the
        config. If a matching set of name and password is found, the user
        is made an oper and notified of this. IF there is no match found,
        the user is notified of an incorrect password, and the attempt 
        is logged.

        """
        for oper in self.config.opers:
            if opname == oper['name'] and pw == oper['pw']:
                user.add_mode('O')
                user.send_numeric(numerics.RPL_YOUREOPER)
                return
        
        print("Failed OPER: ", user.identifier)
        user.send_numeric(numerics.ERR_PASSWDMISMATCH)

    def send_motd(self, user):
        """Send the MOTD to the user."""
        user.send_numeric(numerics.RPL_MOTDSTART, [self.config.hostname])
        for line in self.config.motd.splitlines():
            user.send_numeric(numerics.RPL_MOTD, [line])
        user.send_numeric(numerics.RPL_ENDOFMOTD)

    def send_whois(self, whois_target, reply_user):
        """Send a user WHOIS details on another user."""
        tuser = self.get_user(whois_target)
        self.send_whois_data(tuser, reply_user)
    
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
