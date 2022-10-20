#!/usr/bin/env python

import logging
from flask import url_for


from telegram import (
    BotCommand,
    LoginUrl,
    ParseMode,
    Update,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
from app.flask import create_app
from app.telegram import create_or_update_user
from app.util import Config, Database
from app.toggl import Fetcher

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def start_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        rf"Hi {user.mention_markdown_v2()}\!",
        reply_markup=ForceReply(selective=True),
    )


def connect_command(update: Update, context: CallbackContext) -> None:
    sender = update.message.from_user

    with context.bot_data["database"].get_session() as session:
        user = create_or_update_user(session, sender)

        if user.toggl_user is not None:
            update.message.reply_text(
                f"You are already connected with Toggl Track account {user.toggl_user.email} (#{user.toggl_user.id})!"
            )
        else:
            with context.bot_data["flask"].app_context():
                login_url = LoginUrl(url_for("auth", _scheme="https", _next="connect"))
            keyboard = [
                [
                    InlineKeyboardButton("Open registration page", login_url=login_url),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                "Click to get to the registration dialog:", reply_markup=reply_markup
            )


def disconnect_command(update: Update, context: CallbackContext) -> None:
    sender = update.effective_user

    with context.bot_data["database"].get_session() as session:
        user = create_or_update_user(session, sender)

        if user.toggl_user is None:
            update.message.reply_text(
                "You are not connected with a Toggl Track account."
            )
        else:
            previous_toggl_user = user.toggl_user
            user.toggl_user = None
            user.start = None
            user.enabled = None

            session.commit()
            session.flush()

            update.message.reply_text(
                f"Diconnected from Toggl Track account {previous_toggl_user.email} (#{previous_toggl_user.id})"
            )


def preferences_command(update: Update, context: CallbackContext) -> None:
    sender = update.message.from_user

    with context.bot_data["database"].get_session() as session:
        user = create_or_update_user(session, sender)

        if user.toggl_user is None:
            update.message.reply_text(
                f"Must be connected to a toggl account to use this function"
            )
        else:
            with context.bot_data["flask"].app_context():
                login_url = LoginUrl(
                    url_for("auth", _scheme="https", _next="preferences")
                )
            keyboard = [
                [
                    InlineKeyboardButton("Open preferences page", login_url=login_url),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                "Open user preferences", reply_markup=reply_markup
            )


def fetch_command(update: Update, context: CallbackContext) -> None:
    sender = update.effective_user

    with context.bot_data["database"].get_session() as session:
        user = create_or_update_user(session, sender)

        if user.toggl_user is None:
            update.message.reply_text(
                "Must be connected to a toggl account to use this function"
            )
        else:
            fetcher = Fetcher(session, user.toggl_user)

            organizations = fetcher.update_organizations()
            workspaces = fetcher.update_workspaces()
            time_entries = fetcher.update_timeentries()

        result = ""
        result += f"Organizations: {len(organizations)}\n"
        result += f"Workspaces: {len(workspaces)}\n"
        result += f"TimeEntries: {len(time_entries)}\n"

        update.message.reply_text(result)


def analyze_command(update: Update, context: CallbackContext) -> None:
    sender = update.effective_user

    with context.bot_data["database"].get_session() as session:
        user = create_or_update_user(session, sender)

        if user.toggl_user is None:
            update.message.reply_text(
                "Must be connected to a toggl account to use this function"
            )
        else:
            from calendar import day_abbr
            from datetime import datetime, timedelta, date
            from dateutil.rrule import rrulestr
            from app.models.app import ScheduleException, User, Schedule
            from app.models.toggl import TimeEntry
            from app.repository.app import (
                ScheduleExceptionRepository,
                ScheduleRepository,
            )
            from app.repository.toggl import TimeEntryRepository

            toggl_user = user.toggl_user

            class Day:
                date = None
                target_time = None
                actual_time = None
                exceptions = None

                def __init__(self, date):
                    self.date = date
                    self.target_time = 0
                    self.actual_time = 0
                    self.exceptions = set()

                def delta(self):
                    return self.actual_time - self.target_time

                def __repr__(self):
                    return f"<Day(target_time={self.target_time};actual_time={self.actual_time})>"

            class Week:
                days = None

                def __init__(self, year: int, week: int):
                    self.days = set()
                    self.year = year
                    self.week = week

                def target_time(self) -> int:
                    return sum(map(lambda x: x.target_time, self.days))

                def actual_time(self) -> int:
                    return sum(map(lambda x: x.actual_time, self.days))

                def fullfillment_rate(self) -> float:
                    return (
                        self.actual_time() / self.target_time()
                        if self.target_time() != 0
                        else None
                    )

                def delta(self) -> int:
                    return self.actual_time() - self.target_time()

            def get_datetime_range(start: date, end: date):
                delta = end - start
                result = []

                for i in range(delta.days + 1):
                    dt_day = start + timedelta(days=i)
                    result.append(dt_day)

                return result

            def apply_schedule(
                days: list[Day], schedule: Schedule, start_limit: date, end_limit: date
            ):
                schedule_days = get_datetime_range(
                    max(start_limit, schedule.start),
                    min(
                        end_limit,
                        schedule.end if schedule.end is not None else end_limit,
                    ),
                )
                for schedule_day in schedule_days:
                    if schedule_day.strftime("%Y-%m-%d") in days:
                        days[schedule_day.strftime("%Y-%m-%d")].target_time = getattr(
                            schedule, f"day{schedule_day.weekday()}"
                        )

            def apply_schedule_exception(
                days: list[Day],
                exception: ScheduleException,
                start_limit: date,
                end_limit: date,
            ):
                rrule = rrulestr(exception.rrule, dtstart=exception.start)

                start = datetime.combine(start_limit, datetime.min.time())
                end = datetime.combine(end_limit, datetime.min.time())

                ex_days = list(rrule.between(start, end, inc=True))

                for ex_day in ex_days:
                    day_key = ex_day.strftime("%Y-%m-%d")
                    if day_key in days:
                        days[day_key].target_time = int(
                            days[day_key].target_time * exception.factor
                        )
                        days[day_key].target_time += exception.addend
                        days[day_key].exceptions.add(exception)

            def apply_time_entries(days: list[Day], time_entries: list[TimeEntry]):
                for time_entry in time_entries:
                    day_key = time_entry.start.strftime("%Y-%m-%d")
                    if day_key in days:
                        days[day_key].actual_time += (
                            time_entry.stop - time_entry.start
                        ).seconds

            def format_time(seconds: int):
                mm, ss = divmod(seconds, 60)
                hh, mm = divmod(mm, 60)
                return f"{hh:02}:{mm:02}:{ss:02}"

            def format_percentage(percent: float, precision: int = 2):
                return (
                    f"{round(percent*100, precision): >{4 + precision}}%"
                    if percent is not None
                    else "-" * (5 + precision)
                )

            now = datetime.now()

            schedule_repository = ScheduleRepository(session)
            schedule_exception_repository = ScheduleExceptionRepository(session)

            result = "<pre>"

            for toggl_organization in toggl_user.organizations:
                for toggl_workspace in toggl_organization.workspaces:
                    result += f"User: {toggl_user.fullname} > Org: {toggl_organization.name} > Workspace: {toggl_workspace.name}\n"
                    result += "\n"

                    days = {}
                    delta = now.date() - user.start
                    for i in range(delta.days + 1):
                        dt_day = user.start + timedelta(days=i)
                        day = Day(dt_day)
                        days[dt_day.strftime("%Y-%m-%d")] = day

                    # Get all relevant work schedules

                    schedules = schedule_repository.get_by_date_range(
                        toggl_user, toggl_workspace, user.start, now.date()
                    )

                    for schedule in schedules:
                        apply_schedule(days, schedule, user.start, now.date())

                    for schedule in schedules:
                        result += (
                            f"Start: {schedule.start}; "
                            f"End: {schedule.end}; "
                            f"{day_abbr[0]}: {schedule.day0}; "
                            f"{day_abbr[1]}: {schedule.day1}; "
                            f"{day_abbr[2]}: {schedule.day2}; "
                            f"{day_abbr[3]}: {schedule.day3}; "
                            f"{day_abbr[4]}: {schedule.day4}; "
                            f"{day_abbr[5]}: {schedule.day5}; "
                            f"{day_abbr[6]}: {schedule.day6}; "
                            "\n"
                        )
                    result += "\n"

                    # Schedule Exceptions
                    schedule_exceptions = (
                        schedule_exception_repository.get_by_user_and_workspace(
                            toggl_user=toggl_user, toggl_workspace=toggl_workspace
                        )
                    )
                    for schedule_exception in schedule_exceptions:
                        apply_schedule_exception(
                            days, schedule_exception, user.start, now.date()
                        )

                    # Time Entries
                    time_entry_repository = TimeEntryRepository(session)
                    time_entries = time_entry_repository.get_by_date_range(
                        toggl_user, toggl_workspace, user.start, now
                    )

                    apply_time_entries(days, time_entries)

                    for day, val in days.items():
                        result += f"{day} {day_abbr[val.date.weekday()] } -> Target: {str(val.target_time).rjust(5)}; Actual: {str(val.actual_time).rjust(5)}; Delta: {str(val.delta()).rjust(6)}; Exceptions: {','.join(map(lambda x:f'{x.description} (*{x.factor}, +{x.addend})', val.exceptions))}\n"

                    result += "\n"

                    weeks = {}
                    for day, val in days.items():
                        kw = val.date.isocalendar()

                        if (kw.year, kw.week) not in weeks:
                            weeks[kw.year, kw.week] = Week(
                                kw.year,
                                kw.week,
                            )

                        weeks[kw.year, kw.week].days.add(val)

                    running_delta = 0
                    for week, val in weeks.items():
                        running_delta += val.delta()
                        result += f"{val.year}-{val.week} ({len(val.days)} Days) -> Target: {format_time(val.target_time())}; Actual: {format_time(val.actual_time())}; Delta: {format_time(val.delta())}; FullfillmentRate: {format_percentage(val.fullfillment_rate())}; RunningDelta: {format_time(running_delta)}\n"

            result += "</pre>"

            update.message.reply_text(result, parse_mode=ParseMode.HTML)


def echo(update: Update, context: CallbackContext) -> None:
    sender = update.effective_user

    with context.bot_data["database"].get_session() as session:
        create_or_update_user(session, sender)

    update.message.reply_text(
        "Checkout the menu to see how to interact with this bot.",
    )


def main() -> None:
    config = Config()
    updater = Updater(config.telegram_token)
    flask = create_app(config)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("connect", connect_command))
    dispatcher.add_handler(CommandHandler("disconnect", disconnect_command))
    dispatcher.add_handler(CommandHandler("fetch", fetch_command))
    dispatcher.add_handler(CommandHandler("analyze", analyze_command))
    dispatcher.add_handler(CommandHandler("preferences", preferences_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    dispatcher.bot_data["flask"] = flask
    dispatcher.bot_data["database"] = Database(config.database_uri)

    bot = updater.bot
    bot.set_my_commands(
        commands=[
            BotCommand("/connect", "Connect with your Toggl account"),
            BotCommand("/disconnect", "Disconnect from your Toggl account"),
            BotCommand("/fetch", "Fetch new resources from toggl"),
            BotCommand("/analyze", "Analyze time entries"),
            BotCommand("/preferences", "User preferences"),
        ],
    )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
