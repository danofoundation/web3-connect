from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from eth_account.messages import encode_defunct
from eth_utils import to_bytes
from eth_keys import keys
import random
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app) 
nonceList = {}

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


wallets_ref = db.collection('wallets').document()
wallets = {
    1: "0x3ffca57f5b00074e13f4af9af206aefe35668375",
    2: "0xc4468a3a09deeb31b64ac912c85fcc2a72b4dcb9"
}


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/nonce')
def generate_nonce():
    wallet_address = request.args.get('walletAddress')
    nonce = str(random.randint(1, 10000))
    nonceList[wallet_address] = nonce
    
    wallets_ref.set({'wallet_address': wallet_address})
    return jsonify({'nonce': nonce})

    
@app.route('/verify')
def verify_signature():
    wallet_address = request.args.get('walletAddress')
    signed_nonce = request.args.get('signedNonce')
    nonce = nonceList.get(wallet_address)
    if nonce is None:
        return jsonify({'success': False})

    try:
        message = encode_defunct(text=nonce)
        signed_message = keys.Signature(to_bytes(hexstr=signed_nonce))
        verified_address = signed_message.recover_public_key_from_msg(message).to_checksum_address()

        if wallet_address.lower() == verified_address.lower():
          
            response = make_response(jsonify({'success': True}))
            response.set_cookie('walletAddress', wallet_address)
            return response
        else:
            raise ValueError('Signature verification failed')
    except (ValueError, Exception) as e:
        return jsonify({'success': False, 'error': str(e)})
        


@app.route('/check')
def check_session():
    wallet_address = request.cookies.get('walletAddress')
    if wallet_address:
        return jsonify({'success': True, 'walletAddress': wallet_address})
    else:
        return jsonify({'success': False})

@app.route('/logout')
def logout():
    response = make_response(jsonify({'success': True}))
    response.set_cookie('walletAddress', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(port=3000)
