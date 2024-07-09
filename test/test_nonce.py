import unittest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from firebase_admin import firestore
from app import app  # Replace with your actual Flask app import

class TestGenerateNonceEndpoint(unittest.TestCase):

    def setUp(self):
        # Set up a test client for Flask app testing
        self.client = app.test_client()

    @patch('app.WALLETS_REF')
    def test_generate_nonce_existing_wallet(self, mock_wallets_ref):
        # Mock Firestore document reference and its behavior
        mock_doc_ref = MagicMock()
        mock_doc_ref.exists = True
        mock_doc_ref.update.return_value = None

        mock_wallets_ref.document.return_value = mock_doc_ref

        # Mock request parameters
        wallet_address = '0x39b53676db9683b459435110c9E4DcA083F3a60f'
        mock_request = MagicMock()
        mock_request.args.get.return_value = wallet_address

        with patch('app.request', mock_request):
            # Make a request to /nonce endpoint
            response = self.client.get('/nonce')

        # Validate response status code and content
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('nonce', response_data)
        self.assertIsInstance(response_data['nonce'], str)

        # Verify Firestore document update call with expected parameters
        expected_nonce_id = response_data['nonce']
        expected_update_time = datetime.now()
        mock_doc_ref.update.assert_called_once_with({
            'nonce': expected_nonce_id,
            'updatedAt': expected_update_time
        })

    @patch('app.WALLETS_REF')
    def test_generate_nonce_new_wallet(self, mock_wallets_ref):
        # Mock Firestore document reference and its behavior for a new wallet
        mock_doc_ref = MagicMock()
        mock_doc_ref.exists = False
        mock_doc_ref.set.return_value = None

        mock_wallets_ref.document.return_value = mock_doc_ref

        # Mock request parameters
        wallet_address = '0x39b53676db9683b459435110c9E4DcA083F3a60f'
        mock_request = MagicMock()
        mock_request.args.get.return_value = wallet_address

        with patch('app.request', mock_request):
            # Make a request to /nonce endpoint
            response = self.client.get('/nonce')

        # Validate response status code and content
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('nonce', response_data)
        self.assertIsInstance(response_data['nonce'], str)

        # Verify Firestore document set call with expected parameters
        expected_nonce_id = response_data['nonce']
        expected_creation_time = datetime.now()
        mock_doc_ref.set.assert_called_once_with({
            'wallet_address': wallet_address,
            'nonce': expected_nonce_id,
            'createdAt': expected_creation_time,
            'updatedAt': expected_creation_time
        })

if __name__ == '__main__':
    unittest.main()

