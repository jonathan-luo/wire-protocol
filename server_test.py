import server
from server import list_users
import unittest
from unittest.mock import MagicMock

class TestServerMethods(unittest.TestCase):
    mock_socket = MagicMock()

    def test_List_users_No_other_users_Returns_none(self):
        server.connected_clients = {'user': None}
        self.assertIsNone(list_users(self.__class__.mock_socket, 'user', ''))

    def test_List_users_Has_other_users_no_query_provided_Returns_all_other_users(self):
        server.connected_clients = {'user1': None, 'user2': None}
        self.assertEqual(list_users(self.__class__.mock_socket, 'user1', ''), ['user2'])

    def test_List_users_Has_other_users_query_matches_exists_Returns_matches(self):
        server.connected_clients = {'user1': None, 'user2': None}
        self.assertEqual(list_users(self.__class__.mock_socket, 'user1', 'us*'), ['user2'])

    def test_List_users_Has_other_users_query_matches_exists_Returns_matches2(self):
        server.connected_clients = {'user1': None, 'user2': None}
        self.assertEqual(list_users(self.__class__.mock_socket, 'user2', 'u?e?1'), ['user1'])

    def test_List_users_Has_other_users_no_query_matches_Returns_none(self):
        server.connected_clients = {'user1': None, 'user2': None}
        self.assertIsNone(list_users(self.__class__.mock_socket, 'user1', 'p'))

    def test_List_users_Has_other_users_no_query_matches_Returns_none2(self):
        server.connected_clients = {'user1': None, 'user2': None}
        self.assertIsNone(list_users(self.__class__.mock_socket, 'user1', 'u_s'))

if __name__ == '__main__':
    unittest.main()