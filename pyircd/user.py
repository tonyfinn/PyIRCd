from pyircd.ircutils import *
from pyircd.message import *
from pyircd import numerics

import functools

def min_params(num_params):
    """Reply with ERR_NEEDMOREPARAMS if too few parameters are sent in an irc
    message.
    """
    def decorate(func):
        @functools.wraps(func)
        def handler(self, msg):
            if len(msg.params) < num_params:
                self.send_numeric(
                    numerics.ERR_NEEDMOREPARAMS,
                    [msg.command]
                )
            else:
                func(self, msg)
        return handler
    return decorate

class User:

    def __init__(self, nick, username, real_name, host, server, connection):
        self.handle_commands = {
            'PRIVMSG': self.handle_privmsg,
            'JOIN': self.handle_join,
            'PART': self.handle_part,
            'QUIT': self.handle_quit,
            'NAMES': self.handle_names,
            'TOPIC': self.handle_topic,
            'WHO': self.handle_who,
            'WHOIS': self.handle_whois,
            'MODE': self.handle_mode,
            'OPER': self.handle_oper
        }

        self.nick = nick
        self.username = username
        self.real_name = real_name
        self.server = server
        self.connection = connection
        self.host = self.connection.address[0]
        
        self.send_opening_numerics()
        self.server.send_motd(self)
        self.server.send_isupport(self)
        self.channels = []
        self.modes = []

    def send_opening_numerics(self):
        """ Send the opening numerics for a new connection."""
        self.send_numeric(numerics.RPL_WELCOME, 
            [
                self.nick,
                self.username,
                self.host
            ]
        )

        self.send_numeric(numerics.RPL_YOURHOST,
            [
                self.server.config.hostname,
                self.server.config.version
            ]
        )

        self.send_numeric(numerics.RPL_CREATED,
            [
                "in the past." # TODO get creation time.
            ]
        )

        self.send_numeric(numerics.RPL_MYINFO,
            [
                self.server.config.hostname,
                self.server.config.version,
                "",
                ""
            ]
        )

    def send_own_mode(self):
        self.send_numeric(
            numerics.RPL_UMODEIS,
            [''.join(self.modes)]
        )

    @property
    def hostmask(self):
        return self.username + '@' + self.host

    @property
    def identifier(self):
        return self.nick + '!' + self.username + '@' + self.host

    def handle_cmd(self, msg):
        command = msg.split(' ')[0].upper()
        if command in self.handle_commands:
            self.handle_commands[command](msg_from_string(msg))
    
    @min_params(2)
    def handle_privmsg(self, msg):
        """Handle recieving a message from the user"""
        targets = msg.params[0].split(',')
        for target in targets:
            try:
                if is_channel_name(target):
                    self.server.get_channel(target).msg(self, msg.last)
                else:
                    target_user = self.server.get_user(target)
                    target_user.msg(self, target, msg.last)
            except KeyError:
                self.send_numeric(numerics.ERR_NOSUCHNICK, [target])

    @min_params(1)
    def handle_join(self, msg):
        """Handle the user attempting to join a channel"""
        channel = msg.params[0]
        if len(msg.params) > 1:
            key = parts[1]
        try:
            self.server.join_user_to_channel(self, channel)
        except InvalidChannelError:
            self.send_numeric(numerics.ERR_BADCHANMASK, channel)

    @min_params(1)
    def handle_part(self, msg):
        """Handle the user leaving a channel"""
        if len(msg.params) == 2:
            channel, reason = msg.params
        else:
            channel = msg.params[0]
            reason = None

        try:
            self.server.get_channel(channel).part(self, reason)
        except KeyError:
            # Channel doesn't exist, no need to take action.
            pass

    def handle_quit(self, msg):
        """Handle the user quitting from the server"""
        if len(msg.params) == 1:
            reason = msg.params[0]
            self.server.quit_user(self, reason)
        else:
            self.server.quit_user(self)
        self.connection.close()

    def handle_names(self, msg):
        """Handle a request for the names command"""
        if len(msg.params) == 1:
            channels = msg.params[0]
            for channel in channels.split(','):
                chan_obj = self.server.get_channel(channel)
                chan_obj.send_user_list(self)
        else:
            for channel in self.server.channels:
                chan_obj = self.server.get_channel(channel)
                chan_obj.send_user_list(self)

    @min_params(1)
    def handle_topic(self, msg):
        """Handle a request for a channel topic or topic change"""
        channel = msg.params[0]
        try:
            chan_obj = self.server.get_channel(channel)
            if len(msg.params) == 1:
                chan_obj.send_topic(self)
            else:
                new_topic = msg.params[1]
                chan_obj.try_set_topic(self, new_topic)
        except KeyError:
            self.send_numeric(
                numerics.ERR_NOSUCHCHANNEL,
                [channel]
            )

    @min_params(1)
    def handle_mode(self, msg):
        """Handle a mode message."""
        if is_channel_name(msg.params[0]):
            self.handle_channel_mode(msg.params)
        else:
            self.handle_user_mode(msg.params)

    def handle_channel_mode(self, params):
        """Handle a channel mode change attempt."""
        channel = params[0]
        try:
            chan_obj = self.server.get_channel(channel)
        except KeyError:
            self.send_numeric(
                numerics.ERR_NOSUCHCHANNEL,
                [channel]
            )
            return
        if len(params) == 1:
            chan_obj.send_mode_info(self)
        else:
            chan_obj.try_mode_changes(self, params[1])

    def handle_user_mode(self, params):
        nick = params[0]
        if nick != self.nick:
            self.send_numeric(numerics.ERR_USERSDONTMATCH)
            return
        elif len(params) == 1:
            self.send_own_mode()
        else:
            modes = params[1]
            if modes[0] == '+':
                adding = True
            elif modes[0] == '-':
                removing = True
            for mode in modes[1:]:
                if self.can_set_own_mode(mode):
                    if adding:
                        self.modes.append(mode)
                    else:
                        self.modes.remove(mode)

    @min_params(1)
    def handle_who(self, msg):
        """Handle recieving a WHO message."""
        channel = msg.params[0]
        self.server.get_channel(channel).send_who(self)

    @min_params(1)
    def handle_whois(self, msg):
        """Handle a WHOIS message being recieved."""
        targets = msg.params[0]
        for target in targets.split(','):
            self.server.send_whois(target, self)

    @min_params(2)
    def handle_oper(self, msg):
        """Handle a OPER command being recieved."""
        self.server.try_make_oper(self, msg.params[0], msg.params[1])

    def send_numeric(self, numeric, sparams=None, source=None):
        """Send a numeric command to the user"""
        if sparams is None:
            params = [self.nick]
        else:
            message = numeric.message.format(*sparams)
            params = [self.nick] + irc_msg_split(message, False)

        self.send_cmd(
            numeric.num_str,
            params,
            numeric.final_multi, 
            source
        )

    def send_msg(self, message):
        """Send a message object as an IRC message."""
        self.send_raw(str(message))

    def send_cmd(self, command, params, final_param_multi_word=False,
            source=None):
        """Send a command formatted as an IRC message appropriately"""
        if not source:
            source = self.server.config.hostname
        irc_msg = build_irc_msg(command, params, final_param_multi_word,
                source)
        self.send_raw(irc_msg)

    def send_raw(self, message):
        self.connection.send_raw(message)

    def msg(self, source, channel, msg):
        """Send a message to the user"""

        msg = Message('PRIVMSG', [channel, msg], True, source.idenfifier)
        self.send_msg(msg)

    def can_set_own_mode(self, mode):
        """Check if a user can set a mode on themselves."""
        return mode not in ['o', 'O']

    def __str__(self):
        return self.identifier

