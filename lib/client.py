import logging
from telegram import ReplyKeyboardRemove, Update, CallbackQuery
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from dataclasses import dataclass
from datetime import datetime, time
import pytz

import lib.keyboards as kb
import lib.utils as ut
from configs.constants import TZ
from lib.backend import Backend

menu_names = ut.get_menu_names()

# Enable logging
logger = logging.getLogger(__name__)


chose_time_text = """Please input start hour, end hour, frequency and notification minute:

For example: '11 18 3 15' will notify you every day at 11:15, 14:15 and 17:15"""

chose_move_text = "⚙️  chose the move:"

class Client:

    @dataclass()
    class States:
        REGISTER_USER: int
        MAIN_MENU: int
        SETTINGS: int
        NOTIFICATION_TIME: int
        ACTIVATE: int
        DEACTIVATE: int

    def __init__(self, token: str, bd_path: str):
        self.backend = Backend(bd_path)
        self.application = Application.builder().token(token).build()
        self.job_queue = self.application.job_queue
        self.states = self.get_states()

    def get_states(self):
        states = self.States(*range(6))
        return states

    def get_user_schedule(self, user_id) -> str:

        response = self.backend.get_setups(user_id)
        if response.status or len(response.answer) != 1:
            return False
        user_info = response.answer[0]

        if user_info.active_flag:

            text = f"🔔 from {user_info.start_hour} to {user_info.end_hour} every {user_info.frequency} hour"
            text += f" at {user_info.minute} minutes"

            return text
        else:
            return "🔕 notifications is off"

    @staticmethod
    def reset_all_user_jobs(user_id, context: ContextTypes.DEFAULT_TYPE) -> bool:
        for hour in range(24):
            job_name = f"{user_id}_{hour}"
            current_jobs = context.job_queue.get_jobs_by_name(job_name)

            for job in current_jobs:
                job.schedule_removal()
                logger.info(f"Job {job_name=} removed")
        return True

    @staticmethod
    async def notification(context: ContextTypes.DEFAULT_TYPE) -> None:

        job = context.job
        user_id, hour = map(int, job.data.split('_'))
        markup = kb.get_inline_mark()
        await context.bot.send_message(job.user_id, text=f"evaluate your condition", reply_markup=markup)
        logger.info(f"notification sent {job.user_id=}, {hour=}")

    def make_jobs(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        response = self.backend.get_setups(user_id)
        if response.status or len(response.answer) != 1:
            logger.error(f"Due job create {response.status=}, {response.answer=}")
            return False
        settings = response.answer[0]
        if not settings.active_flag:
            logger.error(f"Due job create {settings.active_flag=}")
            return True
        self.reset_all_user_jobs(user_id, context)
        start_hour = settings.start_hour
        end_hour = settings.end_hour
        minute = settings.minute
        frequency = settings.frequency

        notification_times = []

        for hour in range(start_hour, end_hour+1, frequency):

            mark_time = ut.time_to_utc(hour, minute)
            name = f"{user_id}_{hour}"
            days = (0, 1, 2, 3, 4, 5, 6)
            context.job_queue.run_daily(self.notification, mark_time, user_id=user_id, days=days, name=name, data=name)
            logger.info(f"create job for {user_id=} {hour=}, utc:{mark_time=}")
            notification_times.append(mark_time)

        return notification_times

    def initialize_jobs(self) -> None:
        response = self.backend.get_all_active_users()
        if response.status:
            logger.error("can not get_all_active_users ")
            return
        users = response.answer

        for settings in users:
            user_id = settings.telegram_id
            start_hour = settings.start_hour
            end_hour = settings.end_hour
            minute = settings.minute
            frequency = settings.frequency

            for hour in range(start_hour, end_hour, frequency):
                mark_time = ut.time_to_utc(hour, minute)
                name = f"{user_id}_{hour}"
                days = (0, 1, 2, 3, 4, 5, 6)
                self.application.job_queue.run_daily(self.notification, mark_time, user_id=user_id,
                                                     days=days, name=name, data=name)
                logger.info(f"create job for {user_id=} {hour=}, utc:{mark_time=}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.message.from_user.id
        response = self.backend.check_user_existence(user_id)
        if response.status:
            text = "Something crashed, reply bot admin"
            await update.message.reply_text(
                text,
            )
            return

        user_existence = response.answer

        if not user_existence:
            text = "Welcome to the mood marks bot! If you want to receive mark call, please push the Activate button"
            markup = kb.activate()
            await update.message.reply_text(
                text,
                reply_markup=markup
            )

            return self.states.REGISTER_USER

        else:
            text = "Welcome!"
            markup = kb.main_menu()

            await update.message.reply_text(
                text,
                reply_markup=markup
            )
            return self.states.MAIN_MENU

    async def proceed_register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.message.from_user.id
        response = self.backend.add_user(user_id)
        if response.status:
            text = "Something crashed, reply bot admin"
            await update.message.reply_text(
                text,
            )
            return self.states.MAIN_MENU

        text = chose_time_text
        await update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardRemove()
        )

        return self.states.NOTIFICATION_TIME

    async def proceed_notification_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message_text = update.message.text
        try:
            parsed_text = map(int, message_text.strip().split())
            start_hour, end_hour, frequency, minute = parsed_text
        except ValueError:
            text = "Invalid format, try again:"
            await update.message.reply_text(
                text,
            )
            return self.states.NOTIFICATION_TIME

        if (
                start_hour < 0 or end_hour < 0 or minute < 0
                or minute > 60
                or start_hour > end_hour
                or end_hour > 23
                or frequency < 1):
            text = "Invalid format, try again:"
            await update.message.reply_text(
                text,
            )
            return self.states.NOTIFICATION_TIME

        user_id = update.message.from_user.id

        response_1 = self.backend.set_notifications_time(user_id, start_hour, end_hour, minute)
        response_2 = self.backend.set_frequency(user_id, frequency)
        response_3 = self.backend.set_activity(user_id, activity=True)
        if response_1.status or response_2.status or response_3.status:
            text = "Something crashed, reply bot admin"
            await update.message.reply_text(
                text,
            )
            return self.states.MAIN_MENU

        notification_times = self.make_jobs(user_id, context)
        if notification_times == False:

            text = " crashed, reply bot admin"
            await update.message.reply_text(
                text,
            )
            return self.states.MAIN_MENU

        text = "👌 we will notify you\n"
        # for tm in notification_times:
        #     text += str(ut.localize(tm)) + "\n"
        text += "Enjoy your notifications"
        markup = kb.main_menu()
        await update.message.reply_text(
            text,
            reply_markup=markup
        )

        return self.states.MAIN_MENU

    async def push_to_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        user_id = update.message.from_user.id
        response = self.backend.get_setups(user_id)
        if response.status or len(response.answer) != 1:
            text = "Something crashed, reply bot admin"
            await update.message.reply_text(
                text,
            )
            return self.states.MAIN_MENU

        text = self.get_user_schedule(user_id)
        text += "\n" + chose_move_text
        active_flag = response.answer[0].active_flag

        markup = kb.settings(active_flag)
        await update.message.reply_text(
            text,
            reply_markup=markup
        )

        return self.states.SETTINGS

    async def move_to_change_notification_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = chose_time_text
        await update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardRemove()
        )
        return self.states.NOTIFICATION_TIME

    async def proceed_activate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.message.from_user.id
        response = self.backend.set_activity(user_id, activity=True)

        if not self.make_jobs(user_id, context):
            text = "Something crashed, reply bot admin"
            await update.message.reply_text(
                text,
            )
            return self.states.MAIN_MENU

        text = self.get_user_schedule(user_id)

        markup = kb.main_menu()
        await update.message.reply_text(
            text,
            reply_markup=markup
        )

        return self.states.MAIN_MENU

    async def proceed_deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.message.from_user.id
        response = self.backend.set_activity(user_id, activity=False)
        self.reset_all_user_jobs(user_id, context)
        text = "Notifications deactivated!"
        markup = kb.main_menu()
        await update.message.reply_text(
            text,
            reply_markup=markup
        )
        return self.states.MAIN_MENU

    async def proceed_mark_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        mark = int(query.data.split('=')[1])
        user_id = query.from_user.id

        response = self.backend.add_mark(user_id, mark)
        text = "Mark was set"
        markup = kb.dzyn_keyboard()
        await query.edit_message_text(text=text, reply_markup=markup)

        return self.states.MAIN_MENU

    async def process_dzyn_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        text = "clink"
        await query.message.reply_text(
            text,
        )
        return self.states.MAIN_MENU

    async def done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END

    async def test_repeat(self, context):
        start_time = datetime(2023, 12, 1)
        end_time = datetime(2023, 12, 8)
        resp = self.backend.get_users_with_activity(start_time, end_time)
        users = resp.answer
        for user in users:
            resp = self.backend.get_last_marks(user, start_time, end_time)
            last_marks = resp.answer
            for mark in last_marks:
                print(mark.mark)
            await context.bot.send_message(chat_id=user, text='ty_pidor')

    def add_repeat_jobs(self):
        self.job_queue.run_repeating(self.test_repeat, interval=10, first=5)

    def build_conversation_handler(self):
        conv_handler = ConversationHandler(
            allow_reentry=True,
            entry_points=[
                    CommandHandler("start", self.start),
            ],
            states={
                self.states.REGISTER_USER: [
                    MessageHandler(filters.Regex(ut.name_to_reg(menu_names.activate)), self.proceed_register_user),
                ],
                self.states.MAIN_MENU: [
                    MessageHandler(filters.Regex(ut.name_to_reg(menu_names.settings)), self.push_to_settings)
                ],
                self.states.SETTINGS: [
                    MessageHandler(filters.Regex(ut.name_to_reg(menu_names.activate)), self.proceed_activate),
                    MessageHandler(filters.Regex(ut.name_to_reg(menu_names.deactivate)), self.proceed_deactivate),
                    MessageHandler(filters.Regex(ut.name_to_reg(menu_names.change_notification_time)),
                                   self.move_to_change_notification_time),
                ],
                self.states.NOTIFICATION_TIME: [
                    MessageHandler(filters.TEXT, self.proceed_notification_time)
                ]
            },
            fallbacks=[MessageHandler(filters.Regex("^Done$"), self.done)],
        )

        return conv_handler

    def build_application(self):
        self.initialize_jobs()
        conv_handler = self.build_conversation_handler()
        self.application.add_handler(conv_handler)
        dzyn_handler = CallbackQueryHandler(self.process_dzyn_callback, pattern=ut.name_to_reg('dzyn'))
        mark_handler = CallbackQueryHandler(self.proceed_mark_callback, pattern="^mark=")
        self.application.add_handler(dzyn_handler)
        self.application.add_handler(mark_handler)
        self.add_repeat_jobs()
        self.application.run_polling(drop_pending_updates=True)

