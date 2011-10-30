from pyircd.ircutils import *
from pyircd import numerics

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
            'WHOIS': self.handle_whois
        }

        self.nick = nick
        self.username = username
        self.real_name = real_name
        self.server = server
        self.connection = connection
        self.host = self.connection.address[0]
        
        self.send_opening_numerics()
        self.send_motd()
        self.server.send_isupport(self)
        self.channels = []

    def send_opening_numerics(self):
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
    
    def handle_privmsg(self, msg):
        """Handle recieving a message from the user"""
        cmd, target_str, message = irc_msg_split(msg)
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

    def handle_join(self, msg):
        """Handle the user attempting to join a channel"""
        cmd, channel = irc_msg_split(msg)
        try:
            self.server.join_user_to_channel(self, channel)
        except KeyError:
            ### TODO Put numeric response here.
            pass

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

    def handle_topic(self, msg):
        """Handle a request for a channel topic"""
        parts = irc_msg_split(msg)
        if len(parts) == 2:
            cmd, channel = parts
            self.send_channel_topic(channel)
        elif len(parts) == 3:
            cmd, channel, message = parts
            # TODO handle setting channel topics

    def handle_who(self, msg):
        parts = irc_msg_split(msg)
        if len(parts) == 2:
            cmd, channel = parts
            self.server.get_channel(channel).send_who(self)

    def handle_whois(self, msg):
        parts = irc_msg_split(msg)
        if len(parts) == 2:
            cmd, targets = parts
            for target in targets.split(','):
                self.server.send_whois(target, self)

    def send_channel_list(self, channel_name):
        """Send the list of people in a channel to a user"""
        channel = self.server.get_channel(channel_name)
        nicks = [user.nick for user in channel]
        nick_str = ' '.join(nicks)
        self.send_numeric(numerics.RPL_NAMREPLY, [channel_name, nick_str])
        self.send_numeric(numerics.RPL_ENDOFNAMES, [channel_name])

    def send_channel_topic(self, channel_name):
        """Send the user information about a channel topic"""
        channel = self.server.get_channel(channel_name)
        self.send_numeric(numerics.RPL_TOPIC, [channel_name, channel.topic])

    def send_numeric(self, numeric, sparams, source=None):
        """Send a numeric command to the user"""
        self.send_cmd(
            numeric.num_str,
            [self.nick] + irc_msg_split(numeric.message.format(*sparams), False),
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

    def send_motd(self):
        """Send the MOTD to a user"""
        self.send_numeric(numerics.RPL_MOTDSTART, [self.server.config.hostname])
        for line in self.server.config.motd.splitlines():
            self.send_numeric(numerics.RPL_MOTD, [line])
        self.send_numeric(numerics.RPL_ENDOFMOTD, [])
        
    def msg(self, source, channel, msg):
        """Send a message to the user"""
        self.send_cmd('PRIVMSG', [channel, msg], True, source.identifier)

    def __str__(self):
        return self.identifier
