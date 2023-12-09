from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import lib.utils as ut

menu_names = ut.get_menu_names()


def activate() -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_names.activate]
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_names.settings]
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def settings(active_flag: bool) -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_names.change_notification_time]
    ]

    if active_flag:
        keyboard.append([menu_names.deactivate])
    else:
        keyboard.append([menu_names.activate])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_inline_mark() -> InlineKeyboardMarkup:
    row = []
    for ix, emoji in enumerate(['😐', '🤔', '😄', '😎', '🐕']):
        button = InlineKeyboardButton(emoji, callback_data=f'mark={ix}')
        row.append(button)

    markup = InlineKeyboardMarkup([row])
    return markup


def dzyn_keyboard() -> InlineKeyboardMarkup:
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🥂", callback_data='dzyn')]])
    return reply_markup


def get_hours(label: str) -> InlineKeyboardMarkup:
    keyboard = []
    curr_row = []
    for hour in range(24):
        str_hour = '0' + str(hour) if hour < 10 else str(hour)
        button = InlineKeyboardButton(str_hour, callback_data=f"{label}_hour={hour}")
        curr_row.append(button)
        if hour % 4 == 3:
            keyboard.append(curr_row)
            curr_row = []
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def get_frequencies() -> InlineKeyboardMarkup:
    keyboard = []
    curr_row = []
    for freq in range(12):
        button = InlineKeyboardButton(str(freq), callback_data=f"freq={freq}")
        curr_row.append(button)
        if freq % 4 == 3:
            keyboard.append(curr_row)
            curr_row = []
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def get_minutes() -> InlineKeyboardMarkup:
    keyboard = []
    curr_row = []
    for minute in range(0, 60, 5):
        str_minute = '0' + str(minute) if minute < 10 else str(minute)
        button = InlineKeyboardButton(str_minute, callback_data=f"minute={minute}")
        curr_row.append(button)
        if minute % 20 == 15:
            keyboard.append(curr_row)
            curr_row = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

