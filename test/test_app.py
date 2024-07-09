import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from app import app, wallets_ref
import requests

BASE_URL = 'http://localhost:3000'
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client
        
def test_index_route(client):
    """Test the '/' route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"<html" in response.data
    
def test_generate_nonce_new_wallet(client):
    wallet_address = "0x3ffca57f5b00074e13f4af9af206aefe35668375"

    # Mock the Firestore document so it doesn't exist initially
    with patch.object(wallets_ref, 'document') as mock_document:
        mock_document.return_value.get.return_value.exists = False

        response = client.get(f'/nonce?walletAddress={wallet_address}')

        assert response.status_code == 200
        data = response.json
        assert 'nonce' in data
        assert isinstance(data['nonce'], str)

def test_generate_nonce_missing_wallet(client):
    wallet_address = "0xnonexistentwallet"

    # Mock the Firestore document so it appears to not exist
    with patch.object(wallets_ref, 'document') as mock_document:
        mock_document.return_value.get.return_value.exists = False
        mock_document.return_value.update.return_value = None  # Mock the update operation

        response = client.get(f'/nonce?walletAddress={wallet_address}')

        assert response.status_code == 200
        data = response.json
        assert 'nonce' in data
        assert isinstance(data['nonce'], str)

        # Split nonce to get the random number part
        nonce_parts = data['nonce'].split('-')
        random_number = nonce_parts[0]

        # Assert that the wallet address is not in the random number part
        assert wallet_address not in random_number

def test_verify_signature_success(client):
    wallet_address = "0x3ffca57f5b00074e13f4af9af206aefe35668375"
    signed_nonce = "abc123"
    
    # Mock Firestore document retrieval to simulate existing wallet address
    with patch('app.wallets_ref.document') as mock_document:
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {'nonce': '123456'}
        mock_document.return_value.get.return_value = mock_doc

        # Mock signature verification to simulate success
        with patch('app.keys.Signature') as mock_signature:
            mock_signature.return_value.recover_public_key_from_msg.return_value.to_checksum_address.return_value = wallet_address.lower()
            
            response = client.get(f'/verify?walletAddress={wallet_address}&signedNonce={signed_nonce}')
            
            assert response.status_code == 200
            assert response.json['success'] is True
            assert 'walletAddress' in response.headers['Set-Cookie']
                      
def test_verify_signature_wallet_not_found(client):
    wallet_address = "0xnonexistentwallet"
    signed_nonce = "abc123"
    
    # Mock Firestore document retrieval to simulate non-existing wallet address
    with patch('app.wallets_ref.document') as mock_document:
        mock_document.return_value.get.return_value.exists = False
        
        response = client.get(f'/verify?walletAddress={wallet_address}&signedNonce={signed_nonce}')
        
        assert response.status_code == 200
        assert response.json['success'] is False
        assert response.json['error'] == 'Wallet address not found'

def test_verify_existing_wallet():
    wallet_address = '0x3ffca57f5b00074e13f4af9af206aefe35668375'
    response = requests.get(f'{BASE_URL}/verify', params={'walletAddress': wallet_address})
    assert response.status_code == 200
    assert response.json() == {'success': True}

def test_verify_non_existing_wallet():
    wallet_address = '0xNonExistingWalletAddress'
    response = requests.get(f'{BASE_URL}/verify', params={'walletAddress': wallet_address})
    assert response.status_code == 200
    assert response.json() == {'success': False, 'error': 'Wallet address not found'}

def test_verify_missing_wallet():
    response = requests.get(f'{BASE_URL}/verify')
    assert response.status_code == 200
    assert response.json() == {'success': False, 'error': 'Wallet address not found'}  
  
def test_check_session_with_valid_cookie():
    wallet_address = '0x3ffca57f5b00074e13f4af9af206aefe35668375'
    cookies = {'walletAddress': wallet_address}
    response = requests.get(f'{BASE_URL}/check', cookies=cookies)
    
    print(f'Response status code: {response.status_code}')
    print(f'Response JSON: {response.json()}')
    
    assert response.status_code == 200
    assert response.json() == {'success': True, 'walletAddress': wallet_address}
    
def test_check_session_with_invalid_cookie():
    wallet_address = '0xInvalidWalletAddress'
    cookies = {'walletAddress': wallet_address}
    response = requests.get(f'{BASE_URL}/check', cookies=cookies)
    
    print(f'Response status code: {response.status_code}')
    print(f'Response JSON: {response.json()}')
    
    assert response.status_code == 200
    assert response.json() == {'success': False, 'error': 'Wallet address not found in Firestore'}
    
def test_check_session_without_cookie(client):
    # Send the request without the 'walletAddress' cookie
    response = client.get('/check')
    
    assert response.status_code == 200
    assert response.json['success'] is False            

def test_logout(client):
    response = client.get('/logout')
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    