import pytest
from app import app, wallets, nonceList

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
   