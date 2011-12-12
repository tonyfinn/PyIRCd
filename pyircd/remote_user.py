from .base_user import BaseUser

class RemoteUser(BaseUser):

    def __init__(self, nick, username, real_name, host, server):
        self.nick = nick
        self.username = username
        self.real_name = real_name
        self.host = host
        self.server = server
        self.modes = []
        self.channels = []

    def send_msg(self, msg):
        self.server.send_msg(msg)
