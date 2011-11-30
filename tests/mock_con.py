class MockCon():
    def __init__(self, socket=None, address=None, server=None):
        self.socket = socket
        if address is None:
            self.address = ('127.0.0.1', 1337)
        else:
            self.address = address
        self.server = server
        self.unique_id = 0

        self.user = None
        self.nick = None
        
        self.sent_msgs = set()
        self.closed = False

    def add_user(self, user):
        self.user = user

    def send_raw(self, msg):
        self.sent_msgs.add(msg)

    def close(self):
        self.closed = True

    def simulate_recv(self, msg):
        self.user.handle_cmd(msg)
