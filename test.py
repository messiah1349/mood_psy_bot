from lib.chart_builder import MonthDrawer, WeekDrawer
from sqlalchemy import create_engine, select
from lib.backend import MarkProcessor, UserProcessor, Backend
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import io
from PIL import Image
import telegram
from configs.constants import API_TOKEN
from telegram.ext import Updater
import asyncio

bd_path = '/data/main.db'

date_start = datetime(2023, 11, 24)
date_end = datetime(2023, 12, 1, 22)

backend = Backend(bd_path)
#'😐', '🤔', '😄', '😎', '🐕'
res = backend.get_last_marks(telegram_id=256856117, date_start=date_start, date_end=date_end).answer

x_dates = [el.mark_time for el in res]
# x_nums = dates.date2num(x_dates)
y = [el.mark + 1 for el in res]

# month_drawer = MonthDrawer()
# buf = month_drawer.draw(x_dates, y)

week_drawer = WeekDrawer()
buf = week_drawer.draw(x_dates, y)

async def send_photo():
    bot = telegram.Bot(token=API_TOKEN)
    await bot.send_photo(chat_id=46340594, photo=buf)

asyncio.run(send_photo())

