#!/usr/bin/env python

import logging
from flask import url_for
from app.report import analyzer


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

            toggl_user = user.toggl_user

            result, _, _ = analyzer.analyze(session, toggl_user, user)

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
