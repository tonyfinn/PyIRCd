from . import BasicTestCase
from .mock_con import MockCon
from .mock_server import MockConfig
from .mock_user import MockUser
from .mock_channel import MockChannel
from pyircd.net import IRCNet
from pyircd.user import User
from pyircd.channel import Channel
from pyircd.errors import NoSuchUserError, NoSuchChannelError

class MockNetwork:
    def __init__(self, server, handler_class=MockCon):
        self.server = server

    def add_new_user(self):
        self.server.handle_new_connection(MockCon())

class BasicServerTestCase(BasicTestCase):
    def setUp(self):
        self.server = IRCNet(MockConfig(), MockCon, MockNetwork)
        self.source_user = MockUser('source', 'sourceu', 'sourcen',
                server=self.server)
        self.server.netaccess.add_new_user()
        self.target_user = MockUser('target', 'targetu', 'targetn',
                server=self.server)

        self.real_user = User('real', 'realu', 'realn', '127.0.0.1',
                self.server, MockCon())
        self.server.netaccess.add_new_user()

class OnConnectTestCase(BasicServerTestCase):
    def test_used_nicks(self):
        """Test that the server records all nicks as used."""
        self.assert_all_in(['source', 'target'], self.server.used_nicks)

    def test_unique_ids(self):
        """Test that the server doesn't give the same ID to every user.

        NOTE: This is not thorough, only checks two users.
        
        """
        self.assert_not_equal(self.source_user.unique_id,
                self.target_user.unique_id)

class UserLocatingTest(BasicServerTestCase):
    def test_by_unique_id(self):
        """Test that the server can find a user by their unique id."""
        self.assert_equal(self.source_user,
                self.server.users[self.source_user.unique_id],
                'Could not get user by ID')

    def test_by_nick(self):
        """Test that the server can find a user by their nick."""
        self.assert_equal(self.source_user,
                self.server.get_user(self.source_user.nick))

    def test_disconnected_user(self):
        """Test that the right exception is thrown upon not finding a user."""
        with self.assertRaises(NoSuchUserError):
            self.server.get_user('notjoined')

class OperTest(BasicServerTestCase):
    def test_oper_allowed(self):
        """Test whether a user is made an oper if they are allowed be one."""
        self.server.try_make_oper(self.source_user, 'test', 'testpass')
        self.assert_true('O' in self.source_user.modes,
            'User was not made an oper')
        reply = {'command': 381, 'params': None, 'source': None}
        self.assert_true(reply in self.source_user.recieved_cmds,
                'No reply sent on oper')

    def test_oper_forbidden(self):
        """Test that a user is not made an oper with incorrect credentials."""
        self.server.try_make_oper(self.target_user, 'fake', 'nopass')
        self.assert_false('O' in self.target_user.modes,
            'User was made an oper incorrectly.')
        reply = {'command': 464, 'params': None, 'source': None}
        self.assert_true(reply in self.target_user.recieved_cmds,
            'User not notified of incorrect password')
        
class MotdTest(BasicServerTestCase):
    def test_motd(self):
        """Ensure the MOTD is correctly parsed into multiple messages."""
        replies = [
            {'command': 375, 'params': ['example.com'], 'source': None},
            {'command': 372, 'params': ['Welcome.'], 'source': None},
            {'command': 372, 'params': ['PyIRCd testing'], 'source': None},
            {'command': 376, 'params': None, 'source': None}
        ]
        self.server.send_motd(self.source_user)
        self.assert_all_in(replies, self.source_user.recieved_cmds,
                'Missing MOTD response')

class ChannelTest(BasicServerTestCase):
    def test_channel_get_exists(self):
        """Check finding a channel that does exist."""
        tchan = MockChannel('#newchan', self.server)
        self.server.channels['#newchan'] = tchan
        self.assert_equal(self.server.get_channel('#newchan'), tchan,
            'Wrong channel was returned.')

    def test_channel_get_not_exists(self):
        """Check the correct error is given for a non existing channel"""
        with self.assertRaises(NoSuchChannelError):
            self.server.get_channel('#doesnotexist')

class JoinTest(BasicServerTestCase):
    def test_join_existing_channel(self):
        """Test that a user correctly joins an existing channel."""
        tchan = MockChannel('#test', self.server)
        self.server.channels['#test'] = tchan
        self.server.join_user_to_channel(self.source_user, '#test')
        self.assert_true({'user': 'source', 'key': None} in tchan.joins,
            'User was not joined to channel')
        self.assert_true(self.source_user in tchan.topic_sends,
            'User was not sent topic')
        self.assert_true(self.source_user in tchan.userl_sends,
            'User was not sent channel listing')

    def test_join_new_channel(self):
        """Test that a user correctly joins a new channel."""
        self.server.join_user_to_channel(self.source_user, '#testnew')
        self.assert_true('#testnew' in self.server.channels,
            'Channel does not exist')
        chan = self.server.channels['#testnew']
        self.assert_true(self.source_user in chan,
            'User is not in channel')
        self.assert_true(chan.mode_on_user('o', self.source_user),
            'User was not given op priviliges')
