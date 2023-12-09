import os
import pytz
from datetime import time
from dotenv import load_dotenv

load_dotenv()

TZ = 'Europe/Helsinki'
API_TOKEN = os.getenv("MOOD_PSY_BOT_TOKEN", 'aaa')


tz = pytz.timezone(TZ)
month_repeat_time = time(12, 19, 10, tzinfo=tz)
week_repeat_time = time(12, 12, 50, tzinfo=tz)
