from lib.client import Client
from configs.constants import API_TOKEN
from db.tables import initialize_bd 


if __name__ == '__main__':
    bd_path = '/data/main.db'
    initialize_bd()
    client = Client(API_TOKEN, bd_path)
    client.build_application()

