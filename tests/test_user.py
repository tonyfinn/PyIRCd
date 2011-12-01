import unittest

from .mock_con import MockCon
from .mock_server import MockConfig, MockServer
from .mock_user import MockUser
from .mock_channel import MockChannel
from pyircd.user import User

class BasicUserTestCase(unittest.TestCase):
    def setUp(self):
        self.server = MockServer()
        self.con = MockCon()
        self.user = User('nick', 'user', 'name', '127.0.0.1', self.server,
                self.con)
        self.con.add_user(self.user)
        self.fake_user = MockUser('nick2', 'user2', 'name2',
            '127.0.0.1', self.server, MockCon())
        self.fake_channel = MockChannel('#test', self.server)

        self.server.set_return_user(self.fake_user)
        self.server.set_return_channel(self.fake_channel)

    def assertAllIn(self, first_list, second_list, msg=None):
        for x in first_list:
            msg = msg or "Missing element: {}".format(x)
            self.assertTrue(x in second_list, msg)

class OnConnectionTestCase(BasicUserTestCase):

    def test_motd_sent(self):
        """Test that the user prompts for motd on connection."""
        self.assertTrue(
            self.server.motd_sent,
            'User did not try have motd sent')

    def test_isupport_sent(self):
        """Test that the user prompts for ISUPPORT info on connection."""
        self.assertTrue(
            self.server.isupport_sent,
            'User did not try have isupport info sent.'
        )

    def test_connect_numerics(self):
        """Test that the user sends all opening numerics to the client on
        connect"""
        messages = [
            ('001', ':Welcome to the Internet Relay Network nick!user@127.0.0.1'),
            ('002', ':Your host is example.com, running version test-1'),
            ('003', ':This server was created in the past.'),
            ('004', 'example.com test-1 Oov kl')
        ]
        sent_msgs = set([':example.com {} nick {}\r\n'.format(message[0], message[1])
            for message in messages])
        self.assertAllIn(sent_msgs, self.con.sent_msgs, 'Missing numeric welcome message')

class UnknownCommandTestCase(BasicUserTestCase):
    def test_handle_unknown(self):
        """Test that clients are notified of invalid commands."""
        replies = set([
            ':example.com 421 nick MADEUP :Unknown command\r\n',
            ':example.com 421 nick MADEUPMORE :Unknown command\r\n',
        ])
        self.con.simulate_recv('MADEUP')
        self.con.simulate_recv('MADEUPMORE command params :with multi part')
        self.assertAllIn(replies, self.con.sent_msgs)

class UserJoinTest(BasicUserTestCase):
    def test_basic_user_join_valid(self):
        """Test the user correctly joins a channel they are allowed to"""
        self.con.simulate_recv('JOIN #test')
        self.con.simulate_recv('JOIN #testkey pass')
        channel_joins = [
            {'user': 'nick', 'channel': '#test', 'key': None},
            {'user': 'nick', 'channel': '#testkey', 'key': 'pass'}
        ]
        self.assertAllIn(channel_joins, self.server.channel_joins)
        
    def test_invalid_key(self):
        """Test the user notifies the client right on the wrong key."""
        self.con.simulate_recv('JOIN #wrongkey somekey')
        reply = ':example.com 475 nick #wrongkey :Cannot join channel (+k)\r\n'
        self.assertTrue(reply in self.con.sent_msgs,
            'Not informed of bad key')

    def test_full_channel(self):
        """Ensure that the user is notified right when joining a full
        channel."""
        self.con.simulate_recv('JOIN #fullchannel')
        reply = ':example.com 471 nick #fullchannel :Cannot join channel (+l)\r\n'
        self.assertTrue(reply in self.con.sent_msgs)

    def test_multi_join(self):
        """Test joining multiple channels in one command."""
        self.con.simulate_recv('JOIN #mtest1,#mtest2')
        channel_joins = [
            {'user': 'nick', 'channel': '#mtest1', 'key': None },
            {'user': 'nick', 'channel': '#mtest2', 'key': None },
        ]
        self.assertAllIn(channel_joins, self.server.channel_joins)

    def test_multi_join_with_keys(self):
        """Test joining multiple channels, some with keys"""
        self.con.simulate_recv('JOIN #mtestkey,#mtest pass')
        expected_joins = [
            {'user': 'nick', 'channel': '#mtestkey', 'key': 'pass'},
            {'user': 'nick', 'channel': '#mtest', 'key': None},
        ]
        self.assertAllIn(expected_joins, self.server.channel_joins)

class QuitTest(BasicUserTestCase):
    def setUp(self):
        BasicUserTestCase.setUp(self)
        self.con.closed = False

    def test_quit(self):
        """Test quitting without a quit reason"""
        self.con.simulate_recv('QUIT')
        self.assertTrue({'user': 'nick', 'reason': None} in self.server.quits,
            'Server not informed of quitting.')
        self.assertTrue(self.con.closed, 'Connection not closed')

    def test_quit_reason(self):
        """Test quitting with a quit reason"""
        self.con.simulate_recv('QUIT :Because why not')
        self.assertTrue(
            {'user': 'nick', 'reason': 'Because why not'} in self.server.quits,
            'No quit reason found.')

class MsgTest(BasicUserTestCase):
    def test_user_to_user(self):
        """Test messaging from one user to another."""
        self.con.simulate_recv('PRIVMSG nick2 :Here is a message')
        reply = {'from': 'nick', 'channel': 'nick2', 
            'text': 'Here is a message'}
        self.assertTrue(reply in self.fake_user.recieved_msgs,
            'Message was not sent to the test user')

    def test_user_to_channel(self):
        """Test messages from a user to channel."""
        self.con.simulate_recv('PRIVMSG #test :Here is a message')
        reply = {'source': 'nick', 'message': 'Here is a message'}
        self.assertTrue(reply in self.fake_channel.msgs,
            'Message was not sent to the test channel.')

class ModeTest(BasicUserTestCase):
    def test_changing_allowed_mode(self):
        """Test a user adding a mode to themselves with no restrictions."""
        self.con.simulate_recv('MODE nick +i')
        self.assertTrue('i' in self.user.modes,
            'Mode was not set')

    def test_oper_with_mode(self):
        """Ensure users can't make themselves opers."""
        self.con.simulate_recv('MODE nick +O')
        self.assertTrue('i' not in self.user.modes,
            'User was allowed make themselves oper.')

    def test_changing_others_mode(self):
        """Ensure the user is blocked from editing someone elses mode."""
        self.con.simulate_recv('MODE target +i')
        reply = ':example.com 502 nick :Cannot change mode for other users\r\n'
        self.assertTrue(reply in self.con.sent_msgs, 
            'Missing ERR_USERSDONTMATCH in sent_msgs')
