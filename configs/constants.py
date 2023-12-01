import os
from dotenv import load_dotenv

load_dotenv()

TZ = 'Europe/Helsinki'
API_TOKEN = os.getenv("MOOD_PSY_BOT_TOKEN", 'aaa')
