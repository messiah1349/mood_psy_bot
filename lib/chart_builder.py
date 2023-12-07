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
from abc import abstractmethod, ABC

bd_path = '/data/main.db'

date_start = datetime(2023, 11, 28)
date_end = datetime(2023, 11, 30, 22)

backend = Backend(bd_path)
#'😐', '🤔', '😄', '😎', '🐕'
res = backend.get_last_marks(telegram_id=256856117, date_start=date_start, date_end=date_end).answer

x_dates = [el.mark_time for el in res]
y = [el.mark + 1 for el in res]


class ChartBuilder(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def setup_plot(self):
        raise NotImplemented

    def plot(self):
        rule_major, rule_minor, title = self.setup_plot()
        loc_major = dates.RRuleLocator(rule_major)
        loc_minor = dates.RRuleLocator(rule_minor)
        formatter = dates.DateFormatter('%m/%d')

        fig, ax = plt.subplots()
        ax.xaxis.set_major_locator(loc_major)
        ax.xaxis.set_minor_locator(loc_minor)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)
        ax.set_title(title)
        ax.set_ylim(0.5, 5.5)

        return fig, ax

    def get_x_nums(self, x_dates):
        x_nums = dates.date2num(x_dates)
        return x_nums

    def get_trend(self, x_nums, y):
        trend = np.polyfit(x_nums, y, 1)
        fit = np.poly1d(trend)
        x_fit = np.linspace(x_nums.min(), x_nums.max())
        trend_x = dates.num2date(x_fit)
        trend_y = fit(x_fit)
        return trend_x, trend_y

    def draw(self, x_dates, y):
        x_nums = self.get_x_nums(x_dates)
        trend_x, trend_y = self.get_trend(x_nums, y)
        fig, ax = self.plot()
        ax.plot(x_dates, y, 'r*', markersize=12)
        ax.plot(trend_x, trend_y, "r--")
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        return buf
        

class WeekDrawer(ChartBuilder):

    def setup_plot(self):
        rule_major = dates.rrulewrapper(dates.DAILY, interval=1)
        rule_minor = dates.rrulewrapper(dates.HOURLY, interval=4)
        title = 'History of your marks for last week'
        return rule_major, rule_minor, title
        

class MonthDrawer(ChartBuilder):

    def setup_plot(self):
        rule_major = dates.rrulewrapper(dates.DAILY, interval=3)
        rule_minor = dates.rrulewrapper(dates.DAILY, interval=1)
        title = 'History of your marks for last month'
        return rule_major, rule_minor, title

        
week_drawer = WeekDrawer()
buf = week_drawer.draw(x_dates, y)

# month_drawer = MonthDrawer()
# buf = month_drawer.draw(x_dates, y)


async def send_photo():
    bot = telegram.Bot(token=API_TOKEN)
    await bot.send_photo(chat_id=46340594, photo=buf)

asyncio.run(send_photo())


