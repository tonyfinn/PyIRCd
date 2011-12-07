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

    def test_join_message(self):
        """Test that all users within a channel recieve a join message."""
        newchan = Channel('#newchan', self.server)
        newchan.join(self.users[3])
        reply = {'command': 'JOIN', 'params': ['#newchan'], 
                'source': 'user3!user3n@127.0.0.1'}
        self.assert_in(reply, self.users[3].recieved_cmds,
            "User wasn't informed of joining the channel")
        newchan.join(self.users[4])
        r2 = {'command': 'JOIN', 'params': ['#newchan'],
                'source': 'user4!user4n@127.0.0.1'}
        self.assert_in(r2, self.users[3].recieved_cmds,
            "User wasn't told of other user entering channel.")

class PartTest(ChannelTest):
    def setUp(self):
        ChannelTest.setUp(self)
        for user in self.users:
            self.tchan.join(user)

    def test_basic_part(self):
        self.tchan.part(self.users[0])
        self.assert_not_in(self.users[0], self.tchan,
            "User still in channel.")
        reply = {'command': 'PART', 'params': ['#test'],
                'source': 'user0!user0n@127.0.0.1'}
        for user in self.users[1:]:
            self.assert_in(reply, user.recieved_cmds,
                'user {} not informed of channel part.'.format(user.nick))

    def test_part_with_reason(self):
        self.tchan.part(self.users[1], 'Bored now.')
        self.assert_not_in(self.users[1], self.tchan,
            'User still in channel.')
        reply = {'command': 'PART', 'params': ['#test', 'Bored now.'],
                'source': 'user1!user1n@127.0.0.1'}
        for user in self.users[2:]:
            self.assert_in(reply, user.recieved_cmds,
                'user {} not told of part correctly'.format(user.nick))
    
    def test_parting_channel_not_on(self):
        """Test a user parting from a channel they are not on.

        A user should be given a numeric that they are not on that channel in
        this eventuality.

        """
        new_user = MockUser('newu', 'newun', 'newur', '127.0.0.1', 
                self.server, MockCon())
        self.tchan.part(new_user)
        self.assert_in({'command': 442, 'params': ['#test'], 'source': None},
            new_user.recieved_cmds, 
            'User was not told they were not in channel')

class ChannelModeTest(ChannelTest):
    def setUp(self):
        ChannelTest.setUp(self)
        for user in self.users:
            self.tchan.join(user)

    def test_add_simple_mode(self):
        """Test adding a simple mode with no parameters."""
        self.tchan.add_mode('m', self.users[0])
        self.assert_in('m', self.tchan.modes,
            'Mode was not added to channel')
        reply = {'command': 'MODE', 'params': ['#test', '+m'], 'source': None}
        for user in self.users:
            self.assert_in(reply, user.recieved_cmds,
                'User {} was not informed of mode change'.format(user.nick))

    def test_add_limit(self):
        """Test adding a channel limit."""
        self.tchan.add_mode('l', self.users[0], iter(['40']))
        self.assert_equal(40, self.tchan.limit,
            'Limit was not set correctly.')

    def test_add_key(self):
        """Test adding a key to a channel."""
        self.tchan.add_mode('k', self.users[0], iter(['KEY!']))
        self.assert_equal(
            'KEY!', self.tchan.key, 'Key was not set correctly.')

    def test_missing_params(self):
        """Test adding a mode with too few parameters."""
        with self.assertRaises(InsufficientParamsError):
            self.tchan.add_mode('k', self.users[0], iter([]))

    def test_non_int_limit(self):
        """Test trying to set the limit to an invalid value, like bob"""
        self.tchan.add_mode('l', self.users[0], iter(['bob']))
        self.assert_true(
            self.tchan.limit is None, 'Limit was set to invalid value')

    def test_remove_mode(self):
        """Test removing a simple mode from a channel."""
        self.tchan.modes.add('m')
        self.tchan.remove_mode(
            'm', self.users[0])
        self.assert_not_in(
            'm', self.tchan.modes, 'Mode was not removed from the channel')
        reply = {'command': 'MODE', 'params': ['#test', '-m'], 'source': None}
        for user in self.users:
            self.assert_in(
                reply, user.recieved_cmds, 'User was not notified of removal')
    
    def test_remove_limit(self):
        """Test removing the limit from a room."""
        self.tchan.limit = 50
        self.tchan.remove_mode(
            'l', self.users[0], iter(['50']))
        self.assert_true(
            self.tchan.limit is None, 'Limit was not reset with a param')
        self.tchan.limit = 40
        self.tchan.remove_mode(
            'l', self.users[0])
        self.assert_true(
            self.tchan.limit is None, 
            'Limit was not reset without a parameter')
    
    def test_remove_key(self):
        """Test removing the key from a room."""
        self.tchan.key = 'bob'
        self.tchan.remove_mode(
            'k', self.users[0], iter(['bob']))
        self.assert_true(
            self.tchan.key is None, 'Key was not reset with a param')
        self.tchan.key = 'rob'
        self.tchan.remove_mode(
            'k', self.users[0])
        self.assert_true(
            self.tchan.key is None, 
            'Key was not reset without a parameter')

    def test_has_mode_negative(self):
        """Test the has_mode method for checking modes not in a room."""
        self.tchan.key = None
        self.tchan.limit = None
        self.tchan.modes = set()
        modes = ['k', 'l', 'm']
        for mode in modes:
            self.assert_false(
                self.tchan.has_mode(mode),
                'The channel has mode {} which it should not'.format(mode))

    def test_has_mode_positive(self):
        """Test the has_mode method for checking modes in a room."""
        self.tchan.key = 'key'
        self.tchan.limit = 50
        self.tchan.modes = {'m', 's'}
        modes = ['k', 'l', 'm']
        for mode in modes:
            self.assert_true(
                self.tchan.has_mode(mode),
                'The channel does not have mode {}'.format(mode))
