import pytest
import random
from datetime import datetime
from unittest.mock import patch
from flask import jsonify, make_response, request, Flask, session
import concurrent.futures
# Mock Firestore for testing
class MockFirestore:
    def __init__(self):
        self.data = {}

    def document(self, doc_id):
        return MockDocumentReference(self.data, doc_id)

class MockDocumentReference:
    def __init__(self, data, doc_id):
        self.data = data
        self.doc_id = doc_id

    def get(self):
        return MockDocumentSnapshot(self.data.get(self.doc_id, None))

    def update(self, fields):
        self.data[self.doc_id].update(fields)

    def set(self, fields):
        self.data[self.doc_id] = fields

class MockDocumentSnapshot:
    def __init__(self, data):
        self.exists = data is not None
        self.data = data

WALLETS_REF = MockFirestore()

@pytest.fixture
def app():
    app = Flask(__name__)

    @app.route('/nonce')
    def nonce():
        wallet_address = request.args.get('walletAddress')
        nonce = str(random.randint(1, 10000))
        nonce_id = f"{nonce}-{datetime.now().timestamp()}" 
        created_at = datetime.now()

        doc_ref = WALLETS_REF.document(wallet_address)
        doc = doc_ref.get()

        if doc.exists:
            doc_ref.update({
                'nonce': nonce_id,
                'updatedAt': datetime.now()
            })
        else:
            WALLETS_REF.document(wallet_address).set({
                'wallet_address': wallet_address,
                'nonce': nonce_id,
                'createdAt': created_at,
                'updatedAt': created_at
            })

        return jsonify({'nonce': nonce_id})

    @app.route('/verify', methods=['GET'])
    def verify_signature():
        wallet_address = request.args.get('walletAddress')
        doc_ref = WALLETS_REF.document(wallet_address)
        doc = doc_ref.get()

        if doc.exists:
            response = make_response(jsonify({'success': True}))
            response.set_cookie('walletAddress', wallet_address)
            return response
        else:
            return jsonify({'success': False, 'error': 'Wallet address not found'})

    @app.route('/check')
    def check_session():
        wallet_address = request.cookies.get('walletAddress')

        if wallet_address:
            doc_ref = WALLETS_REF.document(wallet_address)
            doc = doc_ref.get()

            if doc.exists:
                return jsonify({'success': True, 'walletAddress': wallet_address})
            else:
                return jsonify({'success': False, 'error': 'Wallet address not found in Firestore'})
        else:
            return jsonify({'success': False})

    @app.route('/disconnect')
    def disconnect():
        response = make_response(jsonify({'success': True}))
        response.set_cookie('walletAddress', '', expires=0)
        return response

    return app


def test_nonce_endpoint(app):
    with app.test_client() as client:
        # Test nonce generation
        wallet_address = 'test_wallet_address'
        response = client.get(f'/nonce?walletAddress={wallet_address}')
        data = response.get_json()

        assert response.status_code == 200
        assert 'nonce' in data

def test_nonce_concurrent_requests(app):
    def make_request(wallet_address):
        with app.test_client() as client:
            response = client.get(f'/nonce?walletAddress={wallet_address}')
            assert response.status_code == 200
            assert 'nonce' in response.get_json()

    wallet_addresses = ['wallet1', 'wallet2', 'wallet3']  
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(make_request, wallet_addresses)

def test_nonce_large_number_of_requests(app):
    with app.test_client() as client:
        num_requests = 100  # Adjust as necessary
        wallet_addresses = [f'wallet{i}' for i in range(num_requests)]
        
        for wallet_address in wallet_addresses:
            response = client.get(f'/nonce?walletAddress={wallet_address}')
            assert response.status_code == 200
            assert 'nonce' in response.get_json()

def test_nonce_update_existing_address(app):
    with app.test_client() as client:
        wallet_address = 'existing_wallet_address'
        initial_response = client.get(f'/nonce?walletAddress={wallet_address}')
        initial_data = initial_response.get_json()

        assert initial_response.status_code == 200
        assert 'nonce' in initial_data

        updated_response = client.get(f'/nonce?walletAddress={wallet_address}')
        updated_data = updated_response.get_json()

        assert updated_response.status_code == 200
        assert 'nonce' in updated_data
        assert updated_data['nonce'] != initial_data['nonce']

def test_verify_endpoint(app):
    with app.test_client() as client:
        # Test verifying signature
        wallet_address = 'test_wallet_address'
        response = client.get(f'/verify?walletAddress={wallet_address}')
        data = response.get_json()

        assert response.status_code == 200
        assert data['success'] == True

def test_verify_wallet_not_found(app):
    with app.test_client() as client:
        wallet_address = 'non_existent_wallet_address'
        response = client.get(f'/verify?walletAddress={wallet_address}')
        
        assert response.status_code == 200
        assert 'success' in response.get_json()
        assert response.get_json()['success'] == False
        assert 'walletAddress' not in response.headers.get('Set-Cookie', '')

def test_verify_concurrent_requests(app):
    def make_request(wallet_address):
        with app.test_client() as client:
            response = client.get(f'/verify?walletAddress={wallet_address}')
            assert response.status_code == 200
            assert 'success' in response.get_json()

    wallet_addresses = ['wallet1', 'wallet2', 'wallet3']  # Add more addresses as needed
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(make_request, wallet_addresses)
        
def test_check_session_endpoint(app):
    with app.test_client() as client:
        # Test checking session without cookie
        response = client.get('/check')
        data = response.get_json()

        assert response.status_code == 200
        assert data['success'] == False

        # Set cookie and test again
        response = client.get('/verify?walletAddress=test_wallet_address')
        assert response.status_code == 200

        response = client.get('/check')
        data = response.get_json()

        assert response.status_code == 200
        assert data['success'] == True
        assert 'walletAddress' in data

def test_check_session_no_cookie(app):
    with app.test_client() as client:
        response = client.get('/check')
        
        assert response.status_code == 200
        assert response.json == {'success': False}

def test_disconnect_endpoint(app):
    with app.test_client() as client:
        # Test disconnecting
        response = client.get('/disconnect')

        assert response.status_code == 200
        assert 'Set-Cookie' in response.headers
        
