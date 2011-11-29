from pyircd import numerics
from pyircd.message import Message
from pyircd.errors import InsufficientParamsError, ChannelFullError, \
BadKeyError, NeedChanOpError

PERSISTENT_MODES = ['b']
PARAM_MODES = ['b', 'o', 'v', 'l', 'k'] # Ban, op, voice, limit, key
SIMPLE_MODES = ['m', 's', 'i', 't'] # Modded, secret, invite only, topic lock
USER_MODES = ['o', 'v']


class Channel:
    def __init__(self, name, server):
        self.name = name
        self.users = []
        self.usermodes = {}
        self.modes = []
        self.server = server
        self.topic = None
        self.limit = None
        self.key = None

    def join(self, user, key=None):
        """Join a user to the channel"""
        if self.key is not None and key != self.key:
            raise BadKeyError(self.name)

        if self.limit is not None and len(self.users) == self.limit:
            raise ChannelFullError(self.name)

        if user not in self:
            self.users.append(user)
            self.send_to_all(
                Message('JOIN', [self.name], source=user.identifier))

    def part(self, user, msg=None):
        """Remove a user from the channel list."""
        self.users.remove(user)

        if user.hostmask in self.usermodes:
            for mode in self.usermodes[user.hostmask][:]:
                if mode not in PERSISTENT_MODES:
                    self.remove_mode_from_user(mode, user)

        user.channels.remove(self)
        if msg is None:
            self.send_to_all(
                Message('PART', [self.name], True, user.identifier))
        else:
            self.send_to_all(
                Message('PART', [self.name, msg], True, user.identifier))
        
        if len(self.users) == 0:
            self.server.remove_channel(self)

    def add_mode(self, mode, user, piter=None, source=None):
        """Add a mode to a channel."""
        if mode in SIMPLE_MODES:
            self.modes.append(mode)
            self.send_to_all(
                Message('MODE', [self.name, '+' + mode], source=source))
        else:
            try:
                param = next(piter)
            except StopIteration:
                raise InsufficientParamsError('MODE')
            if mode == 'l':
                try:
                    self.limit = int(param)
                except ValueError:
                    return # Spec seems to just want modes ignored if not valid
            elif mode == 'k':
                self.key = param
            self.send_to_all(
                Message(
                    'MODE', [self.name, '+' + mode, param], source=source))

    def remove_mode(self, mode, user, piter=None, source=None):
        """Remove a mode from the channel."""
        if mode in SIMPLE_MODES:
            self.modes.remove(mode)
            self.send_to_all(
                Message('MODE', [self.name, '-' + mode], source=source))
        else:
            try:
                param = next(piter)
            except StopIteration:
                raise InsufficientParamsError('MODE')

            if mode == 'l':
                self.limit = None
            elif mode =='k':
                self.key = None
            
            self.send_to_all(
                Message(
                    'MODE', [self.name, '-' + mode, param], source=source))

    def try_add_user_mode(self, user, mode, piter, source=None):
        """Try to add a mode to a user in this channel, checking for privs"""
        try:
            target = next(piter)
        except StopIteration:
            raise InsufficientParamsError('MODE')

        tuser = self.server.get_user(target)
        if tuser in self.users:
            self.add_mode_to_user(mode, tuser, source)
        else: 
            user.send_numeric(
                numerics.ERR_USERNOTINCHANNEL,
                [target, self.name]
            )

    def try_remove_user_mode(self, user, mode, piter, source=None):
        """Try to add a mode to a user in this channel, checking for privs"""
        try:
            target = next(piter)
        except StopIteration:
            raise InsufficientParamsError('MODE')

        tuser = self.server.get_user(target)
        if tuser in self.users:
            self.remove_mode_from_user(mode, tuser, source)
        else: 
            user.send_numeric(
                numerics.ERR_USERNOTINCHANNEL,
                [target, self.name]
            )

    def send_to_all(self, msg):
        """Send a message to every user in this channel."""
        for user in self.users:
            user.send_msg(msg)

    def try_add_mode(self, user, mode, piter, source):
        """Add a mode if the user is allowed to.

        Otherwise tell them they can't.
        """
        if self.can_set_mode(user, mode):
            if mode in USER_MODES:
                self.try_add_user_mode(user, mode, piter, source=source)
            else:
                self.add_mode(mode, user, piter, source=source)
        else:
            raise NeedChanOpError(self.name)

    def try_remove_mode(self, user, mode, piter, source=None):
        """Remove a mode if the user is allowed to.

        Otherwise, tell them they can't.
        """
        if self.can_set_mode(user, mode):
            self.remove_mode(mode, user, piter, source)

    def try_mode_changes(self, user, modes, params=None):
        """Attempts to change a list of modes as provided by MODE."""
        params = [] if params is None else params
        current_param = 0
        adding = (modes[0] == '+')
        removing = (modes[0] == '-')
        querying = (not adding and not removing) # Not used yet
        piter = iter(params) if params is not None else None
            
        for char in modes[1:]:
            if removing:
                self.try_remove_mode(user, char, piter, user.identifier)
            elif adding:
                self.try_add_mode(user, char, piter, user.identifier)

    def can_set_mode(self, user, mode):
        """Check if a given user can set a mode.

        For the moment, it simply allows operators to set all
        modes, and no one else to set any modes.
        """
        return self.mode_on_user('o', user)

    def can_set_topic(self, user):
        """Check if a given user can set the channel topic."""
        return self.mode_on_user('o', user)

    def add_mode_to_user(self, mode, user, source=None, notify=True):
        """Set a mode on a user within this channel."""
        if user.hostmask in self.usermodes:
            self.usermodes[user.hostmask].append(mode)
        else:
            self.usermodes[user.hostmask] = [mode]

        if notify:
            self.notify_mode_change(mode, '+', user, source)


    def remove_mode_from_user(self, mode, user, source=None, notify=True):
        """Remove a mode from a user within this channel."""
        if user.hostmask in self.usermodes:
            self.usermodes[user.hostmask].remove(mode)
            if self.usermodes[user.hostmask] == []:
                del self.usermodes[user.hostmask]
        
        if notify:
            self.notify_mode_change(mode, '-', user, source)

    def notify_mode_change(self, mode, change, user, source=None):
        self.send_to_all(Message(
            'MODE', 
            [self.name, change + mode, user.nick],
            source=source))

    def mode_on_user(self, mode, user):
        """Check if a user has a given mode within this channel."""
        if user.hostmask not in self.usermodes:
            return False
        else:
            return mode in self.usermodes[user.hostmask]

    def has_mode(self, mode):
        """Return whether a channel has a given mode or not."""
        if mode in self.modes:
            return True
        elif mode =='k' and self.key is not None:
            return True
        elif mode =='l' and self.limit is not None:
            return True
        return False

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

    def send_mode_info(self, target):
        """Send the channel's mode info to a user."""

        modes = ''.join(self.modes) # simple modes

        mode_params = []
        if self.limit is not None:
            modes += 'l'
            if self.mode_on_user('o', target):
                mode_params.append(self.limit)

        if self.key is not None:
            modes += 'k'
            if self.mode_on_user('o', target):
                mode_params.append(self.key)

        params = []
        if len(modes) > 0:
            params = [self.name, modes, ' '.join(mode_params)]
        else:
            params = [self.name, '', '']

        target.send_numeric(
            numerics.RPL_CHANNELMODEIS,
            params
        )

    def try_set_topic(self, user, topic):
        """Set the topic if user is permitted.

        Otherwise, tell them that they can't.
        """
        if self.can_set_topic(user):
            if topic == '':
                self.topic = None
            else:
                self.topic = topic

                self.send_to_all(
                    Message('TOPIC', [self.name, topic], True,
                            user.identifier))
        else:
            raise NeedChanOpError(self.name)

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
