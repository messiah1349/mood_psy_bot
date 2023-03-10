from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import lib.utils as ut

menu_names = ut.get_menu_names()


def activate() -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_names.activate]
    ]

    return ReplyKeyboardMarkup(keyboard)


def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_names.settings]
    ]

    return ReplyKeyboardMarkup(keyboard)


def settings(active_flag: bool) -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_names.change_notification_time]
    ]

    if active_flag:
        keyboard.append([menu_names.deactivate])
    else:
        keyboard.append([menu_names.activate])

    return ReplyKeyboardMarkup(keyboard)


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
