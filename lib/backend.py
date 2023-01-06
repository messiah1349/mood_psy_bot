from sqlalchemy import create_engine
from dataclasses import dataclass
from typing import Any
from datetime import datetime
import logging

from db.tables import User, Mark
from configs.definitions import ROOT_DIR
from lib.table_processor import TableProcessor

logger = logging.getLogger(__name__)


@dataclass
class Response:
    """every backend method should return response object"""
    status: int  # 0 status - everything is good, else - there is error
    answer: Any  # result


class MarkProcessor(TableProcessor):

    def __init__(self, engine):
        super().__init__(engine)
        self.table_model = Mark

    def get_max_id(self):
        return self._get_max_value_of_column(self.table_model, 'id')

    def add_mark(self, telegram_id: int, mark: int) -> Response:
        try:
            current_id = self.get_max_id() + 1
            data = {
                'id': current_id,
                'telegram_id': telegram_id,
                'mark': mark,
                'mark_time': datetime.now(),
            }
            self._insert_values(self.table_model, data)
            logger.info(f"{mark=} from {telegram_id=} was inserted to DB")
            return Response(0, current_id)
        except Exception as e:
            logger.error(f"{mark=} from {telegram_id=} \
            was not inserted to DB, exception - {e}")
            return Response(1, e)


class UserProcessor(TableProcessor):

    def __init__(self, engine):
        super().__init__(engine)
        self.table_model = User

    def add_user(self, telegram_id: int) -> Response:
        try:
            data = {
                'telegram_id': telegram_id,
                'frequency': None,
                'start_hour': None,
                'end_hour': None,
                'minute': None,
                'active_flag': False,
            }
            self._insert_values(self.table_model, data)
            logger.info(f"{telegram_id=} was inserted to DB into user table")
            return Response(0, telegram_id)
        except Exception as e:
            logger.error(f"{telegram_id=} was not inserted to DB into user table")
            return Response(1, e)

    def _get_user_info(self, telegram_id: int) -> Response:
        filter_values = {
            'telegram_id': telegram_id
        }
        settings = self._get_filtered_data(self.table_model, filter_values)

        return settings

    def check_user_existence(self, telegram_id: int) -> Response:
        try:
            user_data = self._get_user_info(telegram_id)
            if len(user_data):
                return Response(0, True)
            else:
                return Response(0, False)
        except Exception as e:
            return Response(1, e)

    def set_frequency(self, telegram_id: int, frequency: int):
        filter_values = {
            'telegram_id': telegram_id
        }
        change_values = {
            'frequency': frequency
        }
        try:
            self._change_column_value(self.table_model, filter_values, change_values)
            logger.info(f"{telegram_id=} frequency was set to {frequency}")
            return Response(0, 'OK')
        except Exception as e:
            logger.error(f"{telegram_id=} frequency was not set to {frequency}")
            return Response(1, e)

    def set_notifications_time(self, telegram_id: int, start_hour: int, end_hour: int, minute: int) -> Response:
        filter_values = {
            'telegram_id': telegram_id
        }
        change_values = {
            'start_hour': start_hour,
            'end_hour': end_hour,
            'minute': minute,
        }
        try:
            self._change_column_value(self.table_model, filter_values, change_values)
            logger.info(f"settings {telegram_id=} {start_hour=} {end_hour=} {minute=} was set")
            return Response(0, 'OK')
        except Exception as e:
            logger.error(f"settings {telegram_id=} {start_hour=} {end_hour=} {minute=} was not set")
            return Response(1, e)

    def set_activity(self, telegram_id: int, activity: bool) -> Response:
        filter_values = {
            'telegram_id': telegram_id
        }
        change_values = {
            'active_flag': activity
        }
        try:
            self._change_column_value(self.table_model, filter_values, change_values)
            logger.info(f"{telegram_id=} activity was set to {activity}")
            return Response(0, 'OK')
        except Exception as e:
            logger.error(f"{telegram_id=} activity was not set to {activity}")
            return Response(1, e)

    def get_setups(self, telegram_id: int):
        try:
            user_info = self._get_user_info(telegram_id)
            logger.info(f"for {telegram_id=} settings was returned")
            return Response(0, user_info)
        except Exception as e:
            logger.error(f"for {telegram_id=} settings was not returned")
            return Response(1, e)

    def get_all_active_users(self):
        filter_values = {
            'active_flag': True
        }
        try:
            active_users = self._get_filtered_data(self.table_model, filter_values)
            logger.info(f"active users was returned")
            return Response(0, active_users)
        except Exception as e:
            logger.error(f"active users was not returned")
            return Response(1, e)


class Backend:

    def __init__(self, db_path: str):
        data_base_uri = f"sqlite:///{ROOT_DIR}/{db_path}"
        engine = create_engine(data_base_uri, echo=False, connect_args={"check_same_thread": False})
        self.user_processor = UserProcessor(engine)
        self.mark_processor = MarkProcessor(engine)

    def add_mark(self, telegram_id: int, mark: int) -> Response:
        return self.mark_processor.add_mark(telegram_id, mark)

    def add_user(self, telegram_id: int) -> Response:
        return self.user_processor.add_user(telegram_id)

    def check_user_existence(self, telegram_id: int) -> Response:
        return self.user_processor.check_user_existence(telegram_id)

    def set_frequency(self, telegram_id: int, frequency: int) -> Response:
        return self.user_processor.set_frequency(telegram_id, frequency)

    def set_notifications_time(self, telegram_id: int, start_hour: int, end_hour: int, minute: int) -> Response:
        return self.user_processor.set_notifications_time(telegram_id, start_hour, end_hour, minute)

    def set_activity(self, telegram_id: int, activity: bool) -> Response:
        return self.user_processor.set_activity(telegram_id, activity)

    def get_setups(self, telegram_id: int) -> Response:
        return self.user_processor.get_setups(telegram_id)

    def get_all_active_users(self):
        return self.user_processor.get_all_active_users()
