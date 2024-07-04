import pytest
from app import app, wallets, nonceList, wallets_ref

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client
        
def test_index_route(client):
    """Test the '/' route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"<html" in response.data
    
def test_generate_nonce_valid(client):
    wallet_address = wallets[1]
    response = client.get(f'/nonce?walletAddress={wallet_address}')
    assert response.status_code == 200
    data = response.json
    assert 'nonce' in data
    assert data['nonce'].isdigit() 
    
@pytest.mark.parametrize("wallet_address, expected_status_code", [
    ('0x3ffca57f5b00074e13f4af9af206aefe35668375', 200),  
    ('0xc4468a3a09deeb31b64ac912c85fcc2a72b4dcb9', 200)
])
def test_generate_nonce(client, wallet_address, expected_status_code):
    response = client.get(f'/nonce?walletAddress={wallet_address}')
    assert response.status_code == expected_status_code
    assert response.json['nonce'].isdigit()
    assert wallet_address in nonceList
   
def test_verify_signature_success(client, mocker):
    
    mocker.patch.dict('app.nonceList', {"0x3ffca57f5b00074e13f4af9af206aefe35668375": "123456"})

    mocker.patch('app.keys.Signature.recover_public_key_from_msg').return_value.to_checksum_address.return_value = "0x3ffca57f5b00074e13f4af9af206aefe35668375"
   
    response = client.get('/verify?walletAddress=0x3ffca57f5b00074e13f4af9af206aefe35668375&signedNonce=abc123')

    assert response.status_code == 200
    #REVIEW - return False
    assert response.json['success'] is True
    assert response.json['error'] is None
    assert 'walletAddress' in response.headers['Set-Cookie']
    
# Test case for /check endpoint
def test_check_session_with_cookie(client):
    # Set the cookie in the request
    response = client.get('/check', headers={'Cookie': 'walletAddress=0x3ffca57f5b00074e13f4af9af206aefe35668375'})
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['walletAddress'] == '0x3ffca57f5b00074e13f4af9af206aefe35668375'

def test_check_session_without_cookie(client):
    response = client.get('/check')
    
    assert response.status_code == 200
    assert response.json['success'] is False

# Test case for /logout endpoint
def test_logout(client):
    response = client.get('/logout')
    
    assert response.status_code == 200
    assert response.json['success'] is True
    
    cookies = response.headers.getlist('Set-Cookie')
    assert any(cookie.startswith('walletAddress=') and 'Expires=Thu, 01 Jan 1970 00:00:00 GMT' in cookie for cookie in cookies)