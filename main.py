from web3 import Web3
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import os
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

infura_url = os.getenv('INFURA_URL')


w3 = Web3(Web3.HTTPProvider(infura_url))


def check_web3_connection():
    result = w3.is_connected()
    return result



if __name__ == '__main__':
    connection_status = check_web3_connection()
    print('Web3 is connected:', connection_status)