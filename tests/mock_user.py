class MockUser:
    def __init__(self, nick='nick', username='user', realname='name',
            host='127.0.0.1', server=None, connection=None):
        self.server = server
        self.connection = connection
        self.nick = nick
        self.username = username
        self.real_name = realname
        self.host = host
        self.hostmask = username + '@' + host
        self.identifier = self.nick + '!' + self.hostmask

        self.unique_id = self.server.highest_unique_id
        self.server.connect_user(self)

        self.modes = []
        self.recieved_msgs = []
        self.recieved_cmds = []

    def add_mode(self, mode):
        self.modes.append(mode)

    def send_msg(self, message):
        self.recieved_cmds.append({'command': msg.command, 'params':
                msg.params, 'source': msg.source})

    def send_cmd(self, command, params, source=None, ignore=None):
        self.recived_cmds.append({'command': command, 'params': params,
            'source': source})

    def send_numeric(self, numeric, params=None, source=None):
        self.recieved_cmds.append({'command': numeric.number, 'params':
            params, 'source': source})

    def msg(self, from_user, channel, content):
        self.recieved_msgs.append({'from': from_user.nick, 'channel': channel,
            'text': content})
