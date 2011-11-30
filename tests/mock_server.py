from pyircd.errors import BadKeyError, ChannelFullError

class MockConfig():
    def __init__(self):
        self.hostname = 'example.com'
        self.port = 1337
        self.version = 'test-1'

class MockServer():
    def __init__(self, config=None):
        self.motd_sent = False
        self.isupport_sent = False
        if config is None:
            self.config = MockConfig()
        self.channel_joins = []
        self.quits = []
        self.whoises = []
        

    def join_user_to_channel(self, user, channel, key):
        if channel == '#wrongkey':
            raise BadKeyError(channel)
        elif channel == '#fullchannel':
            raise ChannelFullError(channel)
        self.channel_joins.append({'user': user.nick, 'channel': channel, 'key':
            key})

    def quit_user(self, user, reason=None):
        self.quits.append({'user': user.nick, 'reason': reason})

    def handle_whois(self, target, asker):
        self.whoises.append({'target': target, 'asker': asker})

    def send_motd(self, target):
        self.motd_sent = True

    def send_isupport(self, target):
        self.isupport_sent = True
