from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from eth_account.messages import encode_defunct
from eth_utils import to_bytes
from eth_keys import keys
import random
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Initialize Firebase app
service_account_path = "./firebase/web3-test-key.json"
try:
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    print("Firebase app initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase app: {e}")

# Initialize Firestore DB
try:
    db = firestore.client()
    wallets_ref = db.collection('wallets')  # Collection reference
    print("Firestore client created successfully")
except Exception as e:
    print(f"Error creating Firestore client: {e}")

nonceList = {}  # Temporarily store nonce in memory
wallets_ref = db.collection('wallets')
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/nonce')
def generate_nonce():
    wallet_address = request.args.get('walletAddress')
    nonce = str(random.randint(1, 10000))
    nonce_id = f"{nonce}-{datetime.now().timestamp()}"

    # Check if wallet address already exists in Firestore
    doc_ref = wallets_ref.document(wallet_address)
    doc = doc_ref.get()

    if doc.exists:
        # Wallet address already exists, update the nonce
        doc_ref.update({'nonce': nonce_id})
    else:
        # Wallet address does not exist, insert a new document
        wallets_ref.document(wallet_address).set({'wallet_address': wallet_address, 'nonce': nonce_id})

    return jsonify({'nonce': nonce_id})

@app.route('/verify')
def verify_signature():
    wallet_address = request.args.get('walletAddress')
    signed_nonce = request.args.get('signedNonce')
    
    # Retrieve document from Firestore based on wallet address
    doc_ref = wallets_ref.document(wallet_address)
    doc = doc_ref.get()
    
    if not doc.exists:
        return jsonify({'success': False, 'error': 'Wallet address not found'})

    # Extract nonce from document data
    nonce = doc.to_dict().get('nonce')

    try:
        message = encode_defunct(text=nonce)
        signed_message = keys.Signature(to_bytes(hexstr=signed_nonce))
        verified_address = signed_message.recover_public_key_from_msg(message).to_checksum_address()

        if wallet_address.lower() == verified_address.lower():
            response = make_response(jsonify({'success': True}))
            response.set_cookie('walletAddress', wallet_address, httponly=True)
            return response
        else:
            raise ValueError('Signature verification failed')
    except (ValueError, Exception) as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/check')
def check_session():
    wallet_address = request.cookies.get('walletAddress')
    if wallet_address:
        return jsonify({'success': True, 'walletAddress': wallet_address}), 200
    else:
        return jsonify({'success': False}), 200

@app.route('/logout')
def logout():
    response = make_response(jsonify({'success': True}))
    response.set_cookie('walletAddress', '', expires=0)  # Clear the 'walletAddress' cookie
    return response
    
if __name__ == '__main__':
    app.run(port=3000)
