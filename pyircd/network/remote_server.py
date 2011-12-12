from . import NoSuchUserError

class RemoteServer:
    def __init__(self, id_, network, con):
        self.network = network
        self.con = con
        self.commands = {
            'NJOIN': self.handle_njoin,
            'SQUIT': self.handle_squit,
            'NICK': self.handle_nick,
            'SERVER': self.handle_server,
            'PRIVMSG': self.handle_privmsg,
            'MODE': self.handle_mode,
            'QUIT': self.handle_quit
        }

    def handle_cmd(self, msg):
        func = self.commands.get(msg.command, self.handle_unknown)
        func(msg)

    def handle_njoin(self, msg):
        pass

    def handle_squit(self, msg):
        pass

    def handle_nick(self, msg):
        pass

    def handle_server(self, msg):
        pass

    def handle_privmsg(self, msg):
        pass

    def handle_mode(self, msg):
        pass

    def handle_quit(self, msg):
        pass

    def handle_unknown(self, msg):
        pass

    def get_user(self, nick):
        for user in self.users:
            if user.nick == nick:
                return user

        raise NoSuchUserError(nick)
