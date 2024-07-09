import unittest
from unittest.mock import patch, MagicMock
from main import check_web3_connection
from app import app, nonceList
class TestWeb3Connection(unittest.TestCase):

    @patch('main.w3')
    def test_web3_connection_success(self, mock_w3):
        mock_w3.is_connected.return_value = True
        result = check_web3_connection()
        self.assertTrue(result)



if __name__ == '__main__':
    unittest.main()
