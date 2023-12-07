import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import io
from abc import abstractmethod, ABC


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
        plt.close()

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
