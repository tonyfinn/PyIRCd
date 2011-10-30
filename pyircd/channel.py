from pyircd import numerics

class Channel:
    def __init__(self, name, server):
        self.name = name
        self.users = []
        self.server = server
        self.topic = ''

    def join(self, user):
        """Join a user to the channel"""
        self.users.append(user)
        for cuser in self.users:
            cuser.send_cmd('JOIN', [self.name, user.nick], source=user.identifier)

    def part(self, user, msg=None):
        """Remove a user from the channel list."""
        self.users.remove(user)
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

    def msg(self, source_user, message): 
        """Send a messsage to the channel."""
        for user in self.users:
            if user != source_user:
                user.msg(source_user, self.name, message)

    def send_who(self, target_user):
        for user in self.users:
            target_user.send_numeric(
                numerics.RPL_WHOREPLY,
                [
                    self.name,
                    user.username,
                    user.host,
                    self.server.config.hostname,
                    user.nick,
                    user.real_name
                ]
            )
        target_user.send_numeric(
            numerics.RPL_ENDOFWHO,
            [
                self.name
            ]
        )

    def send_user_list(self, target):
        """Send a user the list of people in this channel."""
        nicks = [user.nick for user in self]
        nick_str = ' '.join(nicks)
        target.send_numeric(numerics.RPL_NAMREPLY, [self.name, nick_str])
        target.send_numeric(numerics.RPL_ENDOFNAMES, [self.name])

    def send_topic(self, target):
        """Send the current topic to a user."""
        target.send_numeric(numerics.RPL_TOPIC, [self.name, self.topic])

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
