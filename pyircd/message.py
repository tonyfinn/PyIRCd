class InvalidMessageError(Exception):
    pass

class Message:
    def __init__(self, command, params, final_param_multi=False, source=None):
        self.source = source
        self.params = params
        self.command = command
        self.final_param_multi = final_param_multi

    @property
    def last(self):
        return self.params[-1]

    def __str__(self):
        if self.final_param_multi:
            final_param = ':' + self.params[-1]
        else:
            final_param = self.params[-1]

        if self.source:
            prefix = ':' + self.source
        else:
            prefix = ''

        if len(self.params) > 1:
            parts = [prefix, self.command, ' '.join(self.params[:-1]), final_param]
        else:
            parts = [prefix, self.command, final_param]

        return ' '.join(parts).strip() + '\r\n'

def msg_from_string(msg_str):
    """Take an IRC message string and return a Message object. 

    The message needs to be a complete message.
    
    """
    try:
        if msg_str[0] == ':':
            before, after = msg_str.split(' ', 1)
            source = before[1:] # Drop colon
            msg_str = after
        else:
            source = None

        final_part_multi = False
        if ':' in msg_str:
            final_part_multi = True
            before, after = msg_str.split(':', 1)
            params = before.strip().split(' ') + [after]
        else:
            params = [part.strip() for part in msg_str.split(' ')]

        command = params[0]
        params = params[1:]

        return Message(command, params, final_part_multi, source)
    except IndexError:
        raise InvalidMessageError()
        
def irc_msg_split(message, full_message=True):
    """Splits an IRC message (or partial IRC message) into its constituent parts."""
    if message[0] == ':' and full_message:
        message = ''.join(message.split(' ', 1)[1:]) # Drop source for now.

    if ':' in message:
        before, after = message.split(':', 1)
        # This test is because of partial messages
        # that begin with :
        # e.g. RPL_MOTD segments
        if before.strip() != '':
            return before.strip().split(' ') + [after]
        else:
            return [after]
    else:
        return [part.strip() for part in message.split(' ')]
