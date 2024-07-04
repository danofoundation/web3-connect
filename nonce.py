from eth_account.messages import encode_defunct
from eth_account import Account
from dotenv import load_dotenv
import os
load_dotenv()


nonce = "23423"
private_key_1 = os.getenv('WALLET_PRIVATE_KEY_1')
wallet_address_1 = os.getenv('WALLET_ADDRESS_1')
private_key_2 = os.getenv('WALLET_PRIVATE_KEY_2')
wallet_address_2 = os.getenv('WALLET_ADDRESS_2')
# Encode nonce and sign it with the private key
message = encode_defunct(text=nonce)
signed_message = Account.sign_message(message, private_key_1)
signed_nonce = signed_message.signature.hex()
print('Sign nonce from wallet 1: ', signed_nonce)

signed_message_2 = Account.sign_message(message, private_key_2)
signed_nonce_2 = signed_message.signature.hex()
print('Sign nonce from wallet 2: ', signed_nonce_2)