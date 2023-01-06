import os
from lib.client import Client

if __name__ == '__main__':
    API_TOKEN = os.environ["MOOD_PSY_BOT_TOKEN"]
    bd_path = '/data/main.db'
    client = Client(API_TOKEN, bd_path)
    client.build_application()
