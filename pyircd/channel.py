from pyircd import numerics

PERSISTENT_MODES = ['b']

class Channel:
    def __init__(self, name, server):
        self.name = name
        self.users = []
        self.usermodes = {}
        self.modes = []
        self.server = server
        self.topic = None

    def join(self, user):
        """Join a user to the channel"""
        self.users.append(user)
        for cuser in self.users:
            cuser.send_cmd('JOIN', [self.name], source=user.identifier)

    def part(self, user, msg=None):
        """Remove a user from the channel list."""
        self.users.remove(user)

        if user.hostmask in self.usermodes:
            for mode in self.usermodes[user.hostmask][:]:
                if mode not in PERSISTENT_MODES:
                    self.remove_mode_from_user(mode, user)

        user.channels.remove(self)
        for cuser in self.users:
            if msg is None:
                cuser.send_cmd('PART', [self.name], 
                    False,
                    user.identifier)
            else:
                cuser.send_cmd('PART', [self.name, msg],
                    True,
                    user.identifier)
        
        if len(self.users) == 0:
            self.server.remove_channel(self)

    def add_mode(self, mode):
        """Add a mode to a channel."""
        self.modes.append(mode)

    def remove_mode(self, mode):
        """Remove a mode from the channel."""
        self.modes.remove(mode)

    def can_set_mode(self, user, mode):
        """Check if a given user can set a mode.

        For the moment, it simply allows operators to set all
        modes, and no one else to set any modes.
        """
        return self.mode_on_user('o', user)

    def can_set_topic(self, user):
        """Check if a given user can set the channel topic."""
        return self.mode_on_user('o', user)

    def add_mode_to_user(self, mode, user):
        """Set a mode on a user within this channel."""
        if user.hostmask in self.usermodes:
            self.usermodes[user.hostmask].append(mode)
        else:
            self.usermodes[user.hostmask] = [mode]

    def remove_mode_from_user(self, mode, user):
        """Remove a mode from a user within this channel."""
        if user.hostmask in self.usermodes:
            self.usermodes[user.hostmask].remove(mode)
            if self.usermodes[user.hostmask] == []:
                del self.usermodes[user.hostmask]

    def mode_on_user(self, mode, user):
        """Check if a user has a given mode within this channel."""
        if user.hostmask not in self.usermodes:
            return False
        else:
            return mode in self.usermodes[user.hostmask]

    def has_mode(self, mode):
        return mode in self.modes

    def msg(self, source_user, message): 
        """Send a messsage to the channel."""
        for user in self.users:
            if user != source_user:
                user.msg(source_user, self.name, message)

    def send_who(self, target_user):
        for user in self.users:
            mode_prefix = self.get_mode_prefix(user)
            target_user.send_numeric(
                numerics.RPL_WHOREPLY,
                [
                    self.name,
                    user.username,
                    user.host,
                    self.server.config.hostname,
                    user.nick,
                    mode_prefix,
                    user.real_name
                ]
            )
        target_user.send_numeric(
            numerics.RPL_ENDOFWHO,
            [
                self.name
            ]
        )

    def get_mode_prefix(self, user):
        """Get a prefix for a user's nick based on their mode.

        @ for ops
        + for voice.
        """
        if self.mode_on_user('o', user):
            return '@'
        elif self.mode_on_user('v', user):
            return '+'
        else:
            return ''

    def send_user_list(self, target):
        """Send a user the list of people in this channel."""
        nicks = [
            self.get_mode_prefix(user) + user.nick for user in self.users
        ]

        nick_str = ' '.join(nicks)
        target.send_numeric(numerics.RPL_NAMREPLY, [self.name, nick_str])
        target.send_numeric(numerics.RPL_ENDOFNAMES, [self.name])

    def send_topic(self, target):
        """Send the current topic to a user."""
        if self.topic is not None:
            target.send_numeric(
                numerics.RPL_TOPIC, [self.name, self.topic])
        else:
            target.send_numeric(numerics.RPL_NOTOPIC, [self.name])

    def try_set_topic(self, user, topic):
        """Set the topic if user is permitted.

        Otherwise, tell them that they can't.
        """
        if self.can_set_topic(user):
            if topic == '':
                self.topic = None
            else:
                self.topic = topic

            for nuser in self.users:
                nuser.send_cmd(
                    'TOPIC',
                    [self.name, topic],
                    True,
                    user.identifier
                )
        else:
            user.send_numeric(
                numerics.ERR_CHANOPRIVSNEEDED,
                [self.name]
            )

    def __contains__(self, user):
        return user in self.users

    def __iter__(self):
        self.user_iter = 0
        return self

    def __next__(self):
        if self.user_iter >= len(self.users):
            raise StopIteration
        user = self.users[self.user_iter]
        self.user_iter += 1
        return user
