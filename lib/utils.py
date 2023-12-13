import yaml
import pytz
from dataclasses import make_dataclass
from configs.definitions import ROOT_DIR
from configs.constants import TZ
import datetime as dt
from dateutil.relativedelta import relativedelta


def read_config(config_path: str) -> dict:
    with open(config_path, 'r') as file: prime_service = yaml.safe_load(file)

    return prime_service


CONFIG_PATH = ROOT_DIR + '/configs/config.yaml'
config = read_config(CONFIG_PATH)


def get_menu_names():
    menu_naming = config['menu_naming']
    MenuNames = make_dataclass("MenuNames", [(eng, str, rus) for eng, rus in menu_naming.items()])
    menu_names = MenuNames()

    return menu_names

def get_texts():
    text_config = config['texts']
    Texts = make_dataclass("Texts", [(eng, str, rus) for eng, rus in text_config.items()])
    texts = Texts()

    return texts


def name_to_reg(name: str) -> str:
    return f"^{name}$"


def time_to_utc(hour: int, minute: int) -> dt.time:
    current_time = dt.datetime.now()
    local = pytz.timezone(TZ)
    local_dt = local.localize(current_time)
    local_dt = local_dt.replace(hour=hour, minute=minute, second=0)
    utc_time = local_dt.astimezone(pytz.utc).time()
    return utc_time

def date_to_datetime(date_object: dt.date) -> dt.datetime:
    return dt.datetime.fromordinal(date_object.toordinal())

def get_prev_week_borders() -> tuple[dt.datetime, dt.datetime]:
    current_day = dt.date.today()
    prev_week_start = current_day - dt.timedelta(days=7 + current_day.weekday())
    prev_week_end = prev_week_start + dt.timedelta(days=7)
    prev_week_start = date_to_datetime(prev_week_start)
    prev_week_end = date_to_datetime(prev_week_end)
    return prev_week_start, prev_week_end

def get_prev_month_borders() -> tuple[dt.datetime, dt.datetime]:
    current_day = dt.date.today()
    prev_month_day = current_day - dt.timedelta(days=15)
    prev_month_start = prev_month_day.replace(day=1)
    prev_month_end = prev_month_start + relativedelta(months=1)
    prev_month_start = date_to_datetime(prev_month_start)
    prev_month_end = date_to_datetime(prev_month_end)
    return prev_month_start, prev_month_end

    



# def localize(datetime_: dt.time):
#     tz = pytz.timezone(TZ)
#
#     current_time = dt.datetime.now()
#     local = pytz.timezone(TZ)
#     local_dt = local.localize(current_time)
#     local_dt = local_dt.replace(hour=datetime_.hour, minute=datetime_.minute, second=0)
#
#     datetime_.astimezone(tz)
#     return datetime_.astimezone(tz)
