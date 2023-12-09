from datetime import datetime, time
import logging
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from telegram.error import BadRequest
from dataclasses import dataclass

import lib.keyboards as kb
import lib.utils as ut
from configs.constants import week_repeat_time, month_repeat_time
from lib.backend import Backend
from lib.chart_builder import WeekDrawer, MonthDrawer, ChartBuilder

menu_names = ut.get_menu_names()
texts = ut.get_texts()

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
        SET_START_HOUR: int
        SET_END_HOUR: int
        SET_FREQUENCY: int
        SET_MINUTE: int
        ACTIVATE: int
        DEACTIVATE: int

    def __init__(self, token: str, bd_path: str):
        self.backend = Backend(bd_path)
        self.application = Application.builder().token(token).build()
        self.job_queue = self.application.job_queue
        self.states = self.get_states()

    def get_states(self):
        states = self.States(*range(10))
        return states

    def get_user_schedule(self, user_id) -> str|bool:

        response = self.backend.get_setups(user_id)
        if response.status or len(response.answer) != 1:
            return False
        user_info = response.answer[0]

        if user_info.active_flag:

            notification_times = self.get_notification_time_list(
                user_info.start_hour,
                user_info.end_hour,
                user_info.minute,
                user_info.frequency,
            )

            text = f"🔔:\n    "
            text += "\n    ".join(notification_times)

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
            return 0

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

    async def ask_set_start_hour(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = texts.set_start_hour
        await update.message.reply_text(
            text,
            reply_markup=kb.get_hours(label='start')
        )

        return self.states.MAIN_MENU

    async def proceed_start_hour_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        hour = int(query.data.split('=')[1])
        # user_id = query.from_user.id

        context.user_data['start_hour'] = hour

        text = texts.set_end_hour
        markup = kb.get_hours(label='end')
        await query.edit_message_text(text=text, reply_markup=markup)

        return self.states.MAIN_MENU

    async def proceed_end_hour_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        hour = int(query.data.split('=')[1])
        # user_id = query.from_user.id

        if hour < context.user_data['start_hour']:
            text = texts.end_hour_less_start_error
            markup = kb.get_hours(label='end')
            await query.edit_message_text(text=text, reply_markup=markup)
            return self.states.MAIN_MENU

        context.user_data['end_hour'] = hour

        text = texts.set_frequency
        markup = kb.get_frequencies()
        await query.edit_message_text(text=text, reply_markup=markup)

        return self.states.MAIN_MENU

    async def proceed_frequencies_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        frequency = int(query.data.split('=')[1])
        user_id = query.from_user.id

        self.backend.set_frequency(user_id, frequency)
        context.user_data['frequency'] = frequency

        text = texts.set_minute
        markup = kb.get_minutes()
        await query.edit_message_text(text=text, reply_markup=markup)

        return self.states.MAIN_MENU

    @staticmethod
    def get_notification_time_list(start_hour: int, end_hour: int, minute: int, frequency: int) -> list[str]:
        notification_times = []

        for hour in range(start_hour, end_hour + 1, frequency):
            notification_time = time(hour, minute).strftime("%H:%M")
            notification_times.append(notification_time)

        return notification_times

    async def proceed_minute_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        minute = int(query.data.split('=')[1])
        user_id = query.from_user.id
        start_hour=context.user_data['start_hour']
        end_hour=context.user_data['end_hour']
        frequency=context.user_data['frequency']

        self.backend.set_notifications_time(
                telegram_id=user_id, 
                start_hour=start_hour,
                end_hour=end_hour,
                minute=minute,
        )
        context.user_data['minute'] = minute

        text = texts.time_setup_finish

        notification_times = self.get_notification_time_list(
                start_hour=start_hour,
                end_hour=end_hour,
                minute=minute,
                frequency=frequency,
        )
        text += '\n    '
        text += "\n    ".join(notification_times)
        markup = kb.dzyn_keyboard()
        await query.edit_message_text(text=text, reply_markup=markup)

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

        return await self.ask_set_start_hour(update, context)

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

    async def build_report(self, context, drawer: ChartBuilder, start_time: datetime, end_time: datetime) -> None:
        resp = self.backend.get_users_with_activity(start_time, end_time)
        users = resp.answer
        for user in users:
            resp = self.backend.get_last_marks(user, start_time, end_time)
            last_marks = resp.answer
            mark_times = [mark.mark_time for mark in last_marks]
            marks = [mark.mark for mark in last_marks]
            chart = drawer.draw(mark_times, marks)

            try:
                await context.bot.send_photo(chat_id=user, photo=chart)
            except BadRequest as e:
                logger.error("bad request for chat_id = {user}, Exception: {e}")

    async def build_week_report(self, context):
        start_time, end_time = ut.get_prev_week_borders()
        week_drawer = WeekDrawer()
        await self.build_report(context, week_drawer, start_time, end_time)

    async def build_month_report(self, context):
        start_time, end_time = ut.get_prev_month_borders()
        month_drawer = MonthDrawer()
        await self.build_report(context, month_drawer, start_time, end_time)
        
    def add_repeat_jobs(self):
        self.job_queue.run_daily(self.build_week_report, time=week_repeat_time, days=(1,))
        self.job_queue.run_monthly(self.build_month_report, when=month_repeat_time, day=1)

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
                                   self.ask_set_start_hour),
                ],
                self.states.NOTIFICATION_TIME: [
                    MessageHandler(filters.TEXT, self.proceed_notification_time)
                ]
            },
            fallbacks=[MessageHandler(filters.Regex("^Done$"), self.done)],
        )

        return conv_handler

    def add_callbacks(self):
        callbacks = [
            CallbackQueryHandler(self.process_dzyn_callback, pattern=ut.name_to_reg('dzyn')),
            CallbackQueryHandler(self.proceed_mark_callback, pattern="^mark="),
            CallbackQueryHandler(self.proceed_start_hour_callback, pattern="^start_hour="),
            CallbackQueryHandler(self.proceed_end_hour_callback, pattern="^end_hour="),
            CallbackQueryHandler(self.proceed_frequencies_callback, pattern="^freq="),
            CallbackQueryHandler(self.proceed_minute_callback, pattern="^minute="),
        ]
        for callback in callbacks:
            self.application.add_handler(callback)


    def build_application(self):
        self.initialize_jobs()
        conv_handler = self.build_conversation_handler()
        self.application.add_handler(conv_handler)
        self.add_callbacks()
        self.add_repeat_jobs()
        self.application.run_polling(drop_pending_updates=True)

