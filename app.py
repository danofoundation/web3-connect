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

@app.route('/verify', methods=['GET'])
def verify_signature():
    wallet_address = request.args.get('walletAddress')

    # Check if wallet address exists in Firestore
    doc_ref = wallets_ref.document(wallet_address)
    doc = doc_ref.get()

    if doc.exists:
        # If wallet address exists in Firestore, return success
        response = make_response(jsonify({'success': True}))
        response.set_cookie('walletAddress', wallet_address)
        return response
    else:
        # If wallet address does not exist in Firestore, return failure
        return jsonify({'success': False, 'error': 'Wallet address not found'})


@app.route('/check')
def check_session():
    wallet_address = request.cookies.get('walletAddress')
    if wallet_address:
        # Check if wallet address exists in Firestore
        doc_ref = wallets_ref.document(wallet_address)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify({'success': True, 'walletAddress': wallet_address})
        else:
            return jsonify({'success': False, 'error': 'Wallet address not found in Firestore'})
    else:
        return jsonify({'success': False})

@app.route('/logout')
def logout():
    response = make_response(jsonify({'success': True}))
    response.set_cookie('walletAddress', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(port=3000)
