from . import BasicTestCase
from .mock_con import MockCon
from .mock_server import MockConfig
from .mock_user import MockUser
from pyircd.net import IRCNet
from pyircd.user import User

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
