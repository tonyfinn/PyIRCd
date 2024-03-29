from pyircd import numerics
from pyircd.message import Message
from pyircd.errors import InsufficientParamsError, ChannelFullError, \
BadKeyError, NeedChanOpError

# limit, key, ban, exception
PARAM_MODES = ['l', 'k', 'b', 'e'] 
# Modded, secret, invite only, topic lock
SIMPLE_MODES = ['m', 's', 'i', 't', 'n'] 
# Op, voice
USER_MODES = ['o', 'v']


class Channel:
    def __init__(self, name, server):
        self.name = name
        self.users = []
        self.usermodes = {}
        self.modes = set()
        self.server = server
        self.topic = None
        self.limit = None
        self.key = None

        self.ban_masks = []
        self.except_masks = []

    def join(self, user, key=None):
        """Join a user to the channel.

        If the channel needs a key to get in, it will be checked against the
        key parameter. If the key parameter and the needed key do not match
        a BadKeyError will be raised. 

        If the channel has a limit, and it is full, a ChannelFullError will
        be raised.

        If the user manages to join successfully, all other users in the
        channel will be sent a JOIN message to inform them of the new user
        joining the channel.

        """
        
        if user in self:
            return # Already in, do nothing

        if self.key is not None and key != self.key:
            raise BadKeyError(self.name)

        if self.limit is not None and len(self.users) == self.limit:
            raise ChannelFullError(self.name)

        self.users.append(user)
        user.channels.append(self)
        self.send_to_all(
            Message('JOIN', [self.name], source=user))

    def part(self, user, msg=None):
        """Remove a user from the channel.

        If msg is provided, it will be used as the PART message sent to all
        other users in the channel.

        Any modes not in PERSISTENT_MODES that the user has on the channel 
        will be removed. All other users on the channel will be notified of
        their departure from the channel.

        If the user is not on the channel, they will be sent a
        ERR_NOTONCHANNEL numeric to notify them of this.

        """
        if user not in self:
            user.send_numeric(numerics.ERR_NOTONCHANNEL, [self.name])
            return
        self.users.remove(user)

        if user.unique_id in self.usermodes:
            del self.usermodes[user.unique_id]

        user.channels.remove(self)
        if msg is None:
            self.send_to_all(
                Message('PART', [self.name], False, user))
        else:
            self.send_to_all(
                Message('PART', [self.name, msg], True, user))
        
        if len(self.users) == 0:
            self.server.remove_channel(self)

    def add_mode(self, mode, user, piter=None):
        """Add a mode to a channel.

        mode refers to the mode that is currently trying to be set.

        user refers to the user setting the mode.

        piter is an iterator for an iterable that contains parameters for 
        modes may need to be changed. If there isn't enough parameters
        accessible through piter and another parameter is requested,
        this method raises a InsufficientParamsError.

        If the mode change is successful, this method sends a message to all
        users in the channel.

        """
        if mode in SIMPLE_MODES:
            self.modes.add(mode)
            self.send_to_all(
                Message('MODE', [self.name, '+' + mode], source=user))
        elif mode in PARAM_MODES:
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
            elif mode == 'b':
                self.add_mask_to_list(param, self.ban_masks)
            elif mode == 'e':
                self.add_mask_to_list(param, self.except_masks)

            self.send_to_all(
                Message(
                    'MODE', [self.name, '+' + mode, param], source=source))

    def remove_mode(self, mode, user, piter=None):
        """Remove a mode from the channel."""
        if mode in SIMPLE_MODES:
            self.modes.remove(mode)
            self.send_to_all(
                Message('MODE', [self.name, '-' + mode], source=user))
        else:
            if piter is not None:
                try:
                    param = next(piter)
                except StopIteration:
                    param = None
            else:
                param = None

            if mode == 'l':
                self.limit = None
            elif mode =='k':
                self.key = None
            elif mode == 'b':
                self.remove_mask_from_list(param, self.ban_masks)
            elif mode == 'e':
                self.remove_mask_from_list(param, self.except_masks)

            rep_params = [self.name, '-' + mode]
            if param is not None:
                rep_params.append(param)
            
            self.send_to_all(
                Message(
                    'MODE', rep_params, source=user))

    def add_mask_to_list(self, mask, lst):
        """Add a mask to one of the related lists.

        mask is the mask that should be added, lst is the list it should be
        added to.

        This is a helper method that should only be called from MODE handlers.
        If the mask param is None, it raises a InsufficientParamsError.
        Otherwise, it adds the param to the list.

        """
        if mask is None:
            raise InsufficientParamsError('MODE')
        else:
            lst.append(mask)

    def remove_mask_from_list(self, mask, lst):
        """Remove a mask from one of the related lists.

        mask is the user mask that should be removed. lst is the list it 
        should be removed from.

        This is a helper method that should only be called when dealing with
        MODE messages. If the mask param is None, it raises an
        InsufficientParamsError. If the mask is in the list, it removes it
        from the list. If it is not in the list, no action is taken.

        """
        if mask is None:
            raise InsufficentParamsError('MODE')
        else:
            try:
                lst.remove(mask)
            except ValueError:
                pass # No message to be relayed as per spec.

    def try_add_user_mode(self, user, mode, piter):
        """Try to add a mode to a user in this channel, checking for privs"""
        try:
            target = next(piter)
        except StopIteration:
            raise InsufficientParamsError('MODE')

        tuser = self.server.get_user(target)
        if tuser in self.users:
            self.add_mode_to_user(mode, tuser, source=user)
        else: 
            user.send_numeric(
                numerics.ERR_USERNOTINCHANNEL,
                [target, self.name]
            )

    def try_remove_user_mode(self, user, mode, piter):
        """Try to remove a mode from a user in this channel, checking for privs"""
        try:
            target = next(piter)
        except StopIteration:
            raise InsufficientParamsError('MODE')

        tuser = self.server.get_user(target)
        if tuser in self.users:
            self.remove_mode_from_user(mode, tuser, user)
        else: 
            user.send_numeric(
                numerics.ERR_USERNOTINCHANNEL,
                [target, self.name]
            )

    def send_to_all(self, msg, exceptions=None):
        """Send a message to every user in this channel.

        If there are some users that should not recieve this message,
        add them to the exceptions parameter, which is a list of users who
        will be excluded from recieving this message.

        """
        if exceptions is None:
            exceptions = []
        for user in self.users:
            if user not in exceptions:
                user.send_msg(msg)

    def try_add_mode(self, user, mode, piter):
        """Add a mode if the user is allowed to.

        Otherwise tell them they can't.
        """
        if self.can_set_mode(user, mode):
            if mode in USER_MODES:
                self.try_add_user_mode(user, mode, piter)
            else:
                self.add_mode(mode, user, piter)
        else:
            raise NeedChanOpError(self.name)

    def try_remove_mode(self, user, mode, piter):
        """Remove a mode if the user is allowed to.

        Otherwise, tell them they can't.

        """
        if self.can_set_mode(user, mode):
            if mode in USER_MODES:
                self.try_remove_user_mode(user, mode, piter)
            else:
                self.remove_mode(mode, user, piter)
            self.remove_mode(mode, user, piter)

        else:
            raise NeedChanOpError(self.name)

    def try_display_mode(self, user, mode, piter):
        """TODO: Implement ban list display."""
        pass

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
                self.try_remove_mode(user, char, piter)
            elif adding:
                self.try_add_mode(user, char, piter)
            else:
                self.try_display_mode(user, char, piter)

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
        """Set a mode on a user within this channel.
        
        Modes can be set on users that are not in the channel, but most modes
        will be removed when a user leaves a channel. All users in the channel
        will be notified of the mode change.

        """
        if user.unique_id in self.usermodes:
            self.usermodes[user.unique_id].add(mode)
        else:
            self.usermodes[user.unique_id] = set(mode)

        if notify:
            self.notify_mode_change(mode, '+', user, source)


    def remove_mode_from_user(self, mode, user, source=None, notify=True):
        """Remove a mode from a user within this channel."""
        if user.unique_id in self.usermodes:
            self.usermodes[user.unique_id].remove(mode)
            if self.usermodes[user.unique_id] == []:
                del self.usermodes[user.unique_id]
        
        if notify:
            self.notify_mode_change(mode, '-', user, source)

    def notify_mode_change(self, mode, change, user, source=None):

        if source is None:
            source = self.server

        self.send_to_all(Message(
            'MODE', 
            [self.name, change + mode, user.nick],
            source=source))

    def mode_on_user(self, mode, user):
        """Check if a user has a given mode within this channel."""
        if user.unique_id not in self.usermodes:
            return False
        else:
            return mode in self.usermodes[user.unique_id]

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
        message = Message(
            'PRIVMSG', [self.name, message], True,
            source=source_user)

        self.send_to_all(message, exceptions=[source_user])

    def send_who(self, target_user):
        """Send the response to a WHO query to a user."""
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

        If the new topic is blank, the channel topic will be removed. If a
        topic is specified, it will be used as the new topic. All users in the
        channel will be notified of the topic change.

        If the user is not permitted to change the topic, a NeedChanOpError
        will be raised instead of the topic being changed.

        """
        if self.can_set_topic(user):
            if topic == '':
                self.topic = None
            else:
                self.topic = topic

                self.send_to_all(
                    Message('TOPIC', [self.name, topic], True,
                            user))
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
