import unittest

from .mock_con import MockCon
from .mock_server import MockConfig, MockServer
from pyircd.user import User

class BasicUserTestCase(unittest.TestCase):
    def setUp(self):
        self.server = MockServer()
        self.con = MockCon()
        self.user = User('nick', 'user', 'name', '127.0.0.1', self.server,
                self.con)
        self.con.add_user(self.user)

    def assertAllIn(self, first_list, second_list, msg=None):
        for x in first_list:
            msg = msg or "Missing element: {}".format(x)
            self.assertTrue(x in second_list, msg)

class OnConnectionTestCase(BasicUserTestCase):

    def test_motd_sent(self):
        """Test everything the user should do upon connecting."""
        self.assertTrue(
            self.server.motd_sent,
            'User did not try have motd sent')

    def test_isupport_sent(self):
        self.assertTrue(
            self.server.isupport_sent,
            'User did not try have isupport info sent.'
        )

    def test_connect_numerics(self):
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
        replies = set([
            ':example.com 421 nick MADEUP :Unknown command\r\n',
            ':example.com 421 nick MADEUPMORE :Unknown command\r\n',
        ])
        self.con.simulate_recv('MADEUP')
        self.con.simulate_recv('MADEUPMORE command params :with multi part')
        self.assertAllIn(replies, self.con.sent_msgs)

class UserJoinTest(BasicUserTestCase):
    def test_basic_user_join_valid(self):
        self.con.simulate_recv('JOIN #test')
        self.con.simulate_recv('JOIN #testkey pass')
        channel_joins = [
            {'user': 'nick', 'channel': '#test', 'key': None},
            {'user': 'nick', 'channel': '#testkey', 'key': 'pass'}
        ]
        self.assertAllIn(channel_joins, self.server.channel_joins)
        
    def test_invalid_key(self):
        self.con.simulate_recv('JOIN #wrongkey somekey')
        reply = ':example.com 475 nick #wrongkey :Cannot join channel (+k)\r\n'
        self.assertTrue(reply in self.con.sent_msgs,
            'Not informed of bad key')

    def test_full_channel(self):
        self.con.simulate_recv('JOIN #fullchannel')
        reply = ':example.com 471 nick #fullchannel :Cannot join channel (+l)\r\n'
        self.assertTrue(reply in self.con.sent_msgs)

    def test_multi_join(self):
        self.con.simulate_recv('JOIN #mtest1,#mtest2')
        channel_joins = [
            {'user': 'nick', 'channel': '#mtest1', 'key': None },
            {'user': 'nick', 'channel': '#mtest2', 'key': None },
        ]
        self.assertAllIn(channel_joins, self.server.channel_joins)

    def test_multi_join_with_keys(self):
        self.con.simulate_recv('JOIN #mtestkey,#mtest pass')
        expected_joins = [
            {'user': 'nick', 'channel': '#mtestkey', 'key': 'pass'},
            {'user': 'nick', 'channel': '#mtest', 'key': None},
        ]
        self.assertAllIn(expected_joins, self.server.channel_joins)
