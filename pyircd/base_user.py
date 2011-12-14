from .message import Message

class BaseUser:

    @property
    def source_str(self):
        return self.identifier

    @property
    def hostmask(self):
        return self.username + '@' + self.host

    @property
    def identifier(self):
        return self.nick + '!' + self.hostmask

    def add_mode(self, mode):
        self.modes.append(mode)
    
    def msg(self, source, channel, msg):
        """Send a message to the user"""

        msg = Message('PRIVMSG', [channel, msg], True, source)
        self.send_msg(msg)

    def __str__(self):
        return self.identifier

