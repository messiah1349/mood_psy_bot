from sqlalchemy import create_engine, select
from lib.backend import MarkProcessor, UserProcessor, Backend
from datetime import datetime

bd_path = '/data/main.db'

date_start = datetime(2023, 11, 28)
date_end = datetime(2023, 11, 30, 22)

backend = Backend(bd_path)

res = backend.get_last_marks(telegram_id=46340594, date_start=date_start, date_end=date_end)

for row in res.answer:
    print(row.mark)

