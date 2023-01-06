import yaml
import pytz
from dataclasses import make_dataclass
from configs.definitions import ROOT_DIR
from datetime import datetime, time


def read_config(config_path: str) -> dict:
    with open(config_path, 'r') as file:
        prime_service = yaml.safe_load(file)

    return prime_service


CONFIG_PATH = ROOT_DIR + '/configs/config.yaml'
config = read_config(CONFIG_PATH)


def get_menu_names():
    menu_naming = config['menu_naming']
    MenuNames = make_dataclass("MenuNames", [(eng, str, rus) for eng, rus in menu_naming.items()])
    menu_names = MenuNames()

    return menu_names


def name_to_reg(name: str) -> str:
    return f"^{name}$"


def time_to_utc(hour: int, minute: int) -> time:
    current_time = datetime.now()
    local = pytz.timezone('Asia/Yerevan')
    local_dt = local.localize(current_time)
    local_dt = local_dt.replace(hour=hour, minute=minute, second=0)
    utc_time = local_dt.astimezone(pytz.utc).time()
    return utc_time
