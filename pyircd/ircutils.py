import string

CHANNEL_MAX_NAME_LEN = 32
CHANNEL_MIN_NAME_LEN = 3

NICK_MAX_LEN = 16
NICK_MIN_LEN = 3

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

def is_channel_name(name):
    """ Perform a quick check to see if a given string
    looks like a channel name. 
    
    Does not check if the channel name is valid.
    """
    return name.startswith('#') or name.startswith('&')

def is_valid_channel_name(channel):
    """Check to see if a given channel name is valid."""
    if not is_channel_name(channel):
        return False

    test_section = channel[1:]

    if not MIN_CHANNEL_NAME_LEN < len(channel) < MAX_CHANNEL_NAME_LEN:
        return False

    valid_symbols = '#\\|^`[]{}_'
    valid_chars = string.ascii_letters + string.digits + valid_symbols

    for char in channel:
        if char not in valid_chars:
            return False

def is_valid_nick_name(nick):
    """Check to see if a given nick is valid."""
    if not MIN_NICK_LEN < len(nick) < MAX_NICK_LEN:
        return False

    valid_symbols = '\\|^`[]()_'
    valid_chars = string.ascii_letters + string.digits + valid_symbols

def build_irc_msg(command, params, final_param_multi_word=False,
        source=None):
    """Build a string for an IRC message.

    command is the name of the command (e.g. NICK)
    params is a list containing all the parameters, or an empty list if there
    is none.
    final_param_multi_word decides whether the trailing parameter has more
    than one word.
    """

    if final_param_multi_word:
        final_param = ':' + params[-1]
    else:
        final_param = params[-1]

    if source:
        prefix = ':' + source
    else:
        prefix = ''

    if len(params) > 1:
        parts = [prefix, command, ' '.join(params[:-1]), final_param]
    else:
        parts = [prefix, command, final_param]

    return ' '.join(parts).strip() + '\r\n'
