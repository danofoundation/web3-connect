from web3 import Web3
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import os
import random
import firebase_admin
from firebase_admin import credentials, firestore
load_dotenv()

nonceList = {}
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Path to your service account key file
service_account_path = "./firebase/web3-test-key.json"

# Initialize Firebase app
try:
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    print("Firebase app initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase app: {e}")

# Initialize Firestore DB
try:
    db = firestore.client()
    print("Firestore client created successfully")
except Exception as e:
    print(f"Error creating Firestore client: {e}")
#### web3 routes ####
@app.route('/nonce')
def nonce():
    wallet_address = request.args.get('walletAddress')
    nonce = str(random.randint(1, 10000))
    nonce_id = f"{nonce}-{datetime.now().timestamp()}" 
    created_at = datetime.now()
    
    # Check if wallet address already exists in Firestore
    doc_ref = WALLETS_REF.document(wallet_address)
    doc = doc_ref.get()

    if doc.exists:
        # Wallet address already exists, update the nonce and updatedAt
        doc_ref.update({
            'nonce': nonce_id,
            'updatedAt': datetime.now()
        })
    else:
        # Wallet address does not exist, insert a new document with createdAt
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
        # Check if wallet address exists in Firestore
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

### end web3 routes ####