from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()


infura_url = os.getenv('INFURA_URL')


w3 = Web3(Web3.HTTPProvider(infura_url))


def check_web3_connection():
    result = w3.is_connected()
    return result



if __name__ == '__main__':
    connection_status = check_web3_connection()
    print('Web3 is connected:', connection_status)