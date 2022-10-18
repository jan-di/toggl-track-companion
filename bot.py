#!/usr/bin/env python

import logging
from sqlalchemy import false


from telegram import (
    LoginUrl,
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
from models.telegram import User

from util import load_config, Database

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        rf"Hi {user.mention_markdown_v2()}\!",
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("Help!")


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""

    # print(update.message.from_user)

    user_data = update.message.from_user
    tg_user = User(
        id=user_data["id"],
        firstname=user_data["first_name"],
        lastname=user_data["last_name"],
        username=user_data["username"],
        language_code=user_data["language_code"],
        is_premium=user_data["is_premium"] or False,
    )

    with database.get_session() as session:
        session.merge(tg_user)
        session.commit()
        session.flush()

    login_url = LoginUrl("https://127.0.0.1:5000/")
    keyboard = [
        [
            InlineKeyboardButton("Option 1", login_url=login_url),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(update.message.text, reply_markup=reply_markup)


def main() -> None:
    global database

    config = load_config()
    database = Database(config["DATABASE_URI"])

    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(config["TELEGRAM_TOKEN"])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
