import asynchat
import logging
from pyircd.ircutils import *
from pyircd.message import *
from pyircd.user import User
from pyircd import numerics

class IRCCon(asynchat.async_chat): # pragma: no cover
    """Handles a single client's IRC Connection."""
    
    def __init__(self, socket, address, network):
        asynchat.async_chat.__init__(self, sock=socket)
        self.socket = socket
        self.address = address
        self.server = network.local_server
        self.network = network

        self.unique_id = self.server.highest_unique_id
        self.set_terminator(b'\r\n')
        self.user = None
        self.pw = None
        self.con_server = None

        self.nick = None; # Ignored after initial auth

        self.ibuffer = []
        self.obuffer = b''

        self.nick_done = False
        self.user_done = False

        self.handlers = {
            'NICK': self.handle_nick,
            'PASS': self.handle_pass,
            'USER': self.handle_user,
            'SERVER': self.handle_server
        }

    def collect_incoming_data(self, data):
        self.ibuffer.append(data)

    def found_terminator(self):
        msg_bytes = b''.join(self.ibuffer)

        try: 
            mstr = msg_bytes.decode(encoding="utf-8").strip()
            logging.info("Recieved: " + mstr)
            msg = msg_from_string(mstr)
            if msg.command == 'PING':
                # Totally unrelated to the user layer, handle here.
                self.handle_ping(msg)
            elif self.user is None and self.con_server is None:
                try:
                    handler = self.handlers.get(msg.command)
                    handler(msg)
                except KeyError:
                    pass # Unrecognised command, ignore for now.

                if self.nick_done and self.user_done:
                    self.create_user()
            elif self.user is not None:
                self.user.handle_cmd(msg)
            elif self.con_server is not None:
                self.con_server.handle_cmd(msg)
        finally: 
            # Make sure the buffer gets emptied out in case of an error
            # Otherwise the connection ends up continously erroring on the
            # one message.
            self.ibuffer = []

    def handle_ping(self, msg):
        if len(msg.params) == 1:
            info = msg.params[0]
            self.send_raw(build_irc_msg('PONG', [info], True,
                self.network.config.hostname))

    def handle_error(self):
        if self.user:
            self.network.quit_local_user(self.user, "Internet Server Error")
        asynchat.async_chat.handle_error(self)

    def handle_close(self):
        if self.user:
            self.server.quit_user(self.user, "Connection Lost")

    def send_raw(self, msg):
        self.push(msg.encode(encoding="utf-8"))

    def handle_nick(self, msg):
        nick = msg.params[0]
        if nick in self.network.used_nicks:
            self.send_numeric(numerics.ERR_NICKNAMEINUSE, [nick], True)
        else:
            self.nick = nick
            self.nick_done = True

    def handle_user(self, msg):
        if len(msg.params) != 4:
            self.send_numeric(numerics.ERR_NEEDMOREPARAMS, ['USER'], True)
        else:
            username, visibility, ignore, real_name = msg.params
            self.real_name = real_name
            self.username = username
            self.user_done = True

    def handle_pass(self, msg):
        """Handles recieving a PASS command."""
        self.pw = msg.params[0] # TODO others are ignored for now.

    def handle_server(self, msg):
        self.network.add_server(msg.params[0], msg.params[1], msg.params[2], self.pw, self)

    def handle_close(self):
        self.close()

    def send_numeric(self, numeric, sparams, final_param_multi=False,
        source=None):
        """Send a numeric to the user.

        This method should only be used before a user registers when no
        nick exists yet. After registration, use 
        User.send_numeric instead.
        """
        if not source:
            source = self.network.config.hostname

        message = build_irc_msg(
            numeric.num_str,
            irc_msg_split(numeric.message.format(*sparams)),
            final_param_multi,
            source
        )
        self.send_raw(message)

    def create_user(self):
        self.user = User(self.nick, self.username, self.real_name, self.addr,
                self.server, self)
        self.server.connect_user(self.user)
        logging.info(self.user.identifier + " joined.")
