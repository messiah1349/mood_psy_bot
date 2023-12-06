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

date_start = datetime(2023, 11, 28)
date_end = datetime(2023, 11, 30, 22)

backend = Backend(bd_path)
#'😐', '🤔', '😄', '😎', '🐕'
res = backend.get_last_marks(telegram_id=256856117, date_start=date_start, date_end=date_end).answer

x_dates = [el.mark_time for el in res]
x_nums = dates.date2num(x_dates)
y = [el.mark + 1 for el in res]

class ChartBuilder:

    def __init__(self) -> None:
        self.__setup_plot()

    def __setup_plot(self):
        rule_major = dates.rrulewrapper(dates.DAILY, interval=1)
        loc_major = dates.RRuleLocator(rule_major)
        rule_minor = dates.rrulewrapper(dates.HOURLY, interval=4)
        loc_minor = dates.RRuleLocator(rule_minor)
        formatter = dates.DateFormatter('%m/%d')
        
        fig, ax = plt.subplots()
        ax.xaxis.set_major_locator(loc_major)
        ax.xaxis.set_minor_locator(loc_minor)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)
        ax.set_ylim(0.5, 5.5)

        self.fig = fig
        self.ax = ax

    def _x_to_nums(self, x_dates):
        x_nums = dates.date2num(x_dates)
        return x_nums

    def draw_month(self, x, y):
        x_nums = self.get_x_nums(x)
        trend_fitter = self_get_trend_fitter()
        

    def draw_week(self, x, y):
        pass


trend = np.polyfit(x_nums, y, 1)
fit = np.poly1d(trend)

plt.plot(x_dates, y, 'r*', markersize=12)

x_fit = np.linspace(x_nums.min(), x_nums.max())
plt.plot(dates.num2date(x_fit), fit(x_fit), "r--")

buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
# im = Image.open(buf)

async def send_photo():
    bot = telegram.Bot(token=API_TOKEN)
    await bot.send_photo(chat_id=46340594, photo=buf)

asyncio.run(send_photo())


