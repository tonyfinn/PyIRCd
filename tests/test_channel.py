from . import BasicTestCase

from .mock_server import MockConfig, MockServer
from .mock_con import MockCon
from .mock_user import MockUser

from pyircd.channel import Channel
from pyircd.errors import BadKeyError, ChannelFullError, \
InsufficientParamsError

class ChannelTest(BasicTestCase):
    def setUp(self):
        self.server = MockServer(MockConfig())
        self.users = []
        for i in range(5):
            nick = 'user' + str(i)
            name = nick + 'n'
            rn = nick + 'r'
            self.users.append(MockUser(nick, name, rn, server=self.server,
                    connection=MockCon()))
        self.tchan = Channel('#test', self.server)
        self.keychan = Channel('#key', self.server)
        self.keychan.key = 'testkey'
        self.limitchan = Channel('#limit', self.server)
        self.limitchan.limit = 3

class JoinTest(ChannelTest):
    def test_simple_join(self):
        """Test a user joining a channel without any restrictions on them"""
        self.tchan.join(self.users[0])
        self.assert_in(self.users[0], self.tchan)

    def test_keyed_join(self):
        """Test a user joining a keyed channel."""
        self.keychan.join(self.users[1], 'testkey')
        self.assert_in(self.users[1], self.keychan,
            'User with right key not allowed in.')
        with self.assertRaises(BadKeyError):
            self.keychan.join(self.users[2], 'wrongkey')
        self.assert_not_in(self.users[2], self.keychan,
            'User with wrong key allowed in.')

    def test_limit_join(self):
        """Test users joining a channel with a user limit."""
        joining_users = [self.users[i] for i in range(3)]
        [self.limitchan.join(user) for user in joining_users]
        self.assert_all_in(joining_users, self.limitchan,
            'Too few users allowed in')

        with self.assertRaises(ChannelFullError):
            self.limitchan.join(self.users[3])
