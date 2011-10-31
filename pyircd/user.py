from pyircd.ircutils import *
from pyircd import numerics

import functools

def min_params(num_params):
    """Reply with ERR_NEEDMOREPARAMS if too few parameters are sent in an irc
    message.
    """
    def decorate(func):
        @functools.wraps(func)
        def handler(self, msg):
            parts = irc_msg_split(msg)
            if len(parts) < num_params:
                self.send_numeric(
                    numerics.ERR_NEEDMOREPARAMS,
                    [parts[0]]
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
            'MODE': self.handle_mode
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
            self.handle_commands[command](msg)
    
    @min_params(3)
    def handle_privmsg(self, msg):
        """Handle recieving a message from the user"""
        cmd, target_str, message = irc_msg_split(msg)[:3]
        targets = target_str.split(',')
        for target in targets:
            try:
                if is_channel_name(target):
                    self.server.get_channel(target).msg(self, message)
                else:
                    target_user = self.server.get_user(target)
                    target_user.msg(self, target, message)
            except KeyError:
                # TODO Put numeric response here. 
                pass

    @min_params(2)
    def handle_join(self, msg):
        """Handle the user attempting to join a channel"""
        parts = irc_msg_split(msg)
        
        cmd, channel = parts[:2]
        if len(parts) > 2:
            key = parts[3]
        try:
            self.server.join_user_to_channel(self, channel)
        except KeyError:
            ### TODO Put numeric response here.
            pass

    @min_params(2)
    def handle_part(self, msg):
        """Handle the user leaving a channel"""
        parts = irc_msg_split(msg)
        if len(parts) == 3:
            cmd, channel, reason = parts
        else:
            cmd, channel = parts
            reason = None

        try:
            self.server.get_channel(channel).part(self, reason)
        except KeyError:
            # Channel doesn't exist, no need to take action.
            pass

    def handle_quit(self, msg):
        """Handle the user quitting from the server"""
        parts = irc_msg_split(msg)
        if len(parts) == 2:
            cmd, reason = parts
            self.server.quit_user(self, reason)
        else:
            self.server.quit_user(self)
        self.connection.close()

    def handle_names(self, msg):
        """Handle a request for the names command"""
        parts = irc_msg_split(msg)
        if len(parts) == 2:
            cmd, channels = parts
            for channel in channels.split(','):
                self.send_channel_list(channel)
        else:
            for channel in self.server.channels:
                self.send_channel_list(channel)

    @min_params(2)
    def handle_topic(self, msg):
        """Handle a request for a channel topic or topic change"""
        parts = irc_msg_split(msg)
        cmd, channel = parts[:2]
        try:
            chan_obj = self.server.get_channel(channel)
            if len(parts) == 2:
                chan_obj.send_topic(self)
            else:
                new_topic = parts[2]
                chan_obj.try_set_topic(self, new_topic)
        except KeyError:
            self.send_numeric(
                numerics.ERR_NOSUCHCHANNEL,
                [channel]
            )

    @min_params(2)
    def handle_mode(self, msg):
        """Handle a mode message."""
        parts = irc_msg_split(msg)
        if is_channel_name(parts[1]):
            self.handle_channel_mode(parts)
        else:
            self.handle_user_mode(parts)

    def handle_channel_mode(self, msg_parts):
        """Handle a channel mode change attempt."""
        channel = msg_parts[1]
        try:
            chan_obj = self.server.get_channel(channel)
        except KeyError:
            self.send_numeric(
                numerics.ERR_NOSUCHCHANNEL,
                [channel]
            )
            return
        if len(msg_parts) == 2:
            chan_obj.send_mode_info(self)
        else:
            chan_obj.try_mode_changes(self, msg_parts[2])

    def handle_user_mode(self, msg_parts):
        cmd, nick = msg_parts[:2]
        if nick != self.nick:
            self.send_numeric(numerics.ERR_USERSDONTMATCH)
            return
        elif len(msg_parts) == 2:
            self.send_own_mode()
        else:
            modes = msg_parts[2]
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

    @min_params(2)
    def handle_who(self, msg):
        """Handle recieving a WHO message."""
        parts = irc_msg_split(msg)
        cmd, channel = parts[:2]
        self.server.get_channel(channel).send_who(self)

    @min_params(2)
    def handle_whois(self, msg):
        """Handle a WHOIS message being recieved."""
        parts = irc_msg_split(msg)
        if len(parts) >= 2: 
            # Handle some clients adding extra params.
            cmd, targets = parts[:2]
            for target in targets.split(','):
                self.server.send_whois(target, self)

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
        self.send_cmd('PRIVMSG', [channel, msg], True, source.identifier)

    def can_set_own_mode(self, mode):
        """Check if a user can set a mode on themselves."""
        return mode not in ['o', 'O']

    def __str__(self):
        return self.identifier

