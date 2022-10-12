# #!/usr/bin/env python
# # pylint: disable=C0116,W0613

# import logging
# from sqlalchemy import false

# from telegram import Update, ForceReply
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
# from models.telegram_user import TelegramUser
# from util.db import Session

# # Enable logging
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
# )

# logger = logging.getLogger(__name__)


# # Define a few command handlers. These usually take the two arguments update and
# # context.
# def start(update: Update, context: CallbackContext) -> None:
#     """Send a message when the command /start is issued."""
#     user = update.effective_user
#     update.message.reply_markdown_v2(
#         fr'Hi {user.mention_markdown_v2()}\!',
#         reply_markup=ForceReply(selective=True),
#     )


# def help_command(update: Update, context: CallbackContext) -> None:
#     """Send a message when the command /help is issued."""
#     update.message.reply_text('Help!')


# def echo(update: Update, context: CallbackContext) -> None:
#     """Echo the user message."""

#     update.message.reply_text(update.message.text)

#     print(update.message.from_user)

#     user_data = update.message.from_user
#     tg_user = TelegramUser(
#         id=user_data['id'],
#         firstname=user_data['first_name'],
#         lastname=user_data['last_name'],
#         username=user_data['username'],
#         language_code=user_data['language_code'],
#         is_premium=user_data['is_premium'] or False
#     )

#     session = Session()
#     session.merge(tg_user)
#     session.commit()
#     session.flush()


# def main() -> None:
#     """Start the bot."""
#     # Create the Updater and pass it your bot's token.
#     updater = Updater("")

#     # Get the dispatcher to register handlers
#     dispatcher = updater.dispatcher

#     # on different commands - answer in Telegram
#     dispatcher.add_handler(CommandHandler("start", start))
#     dispatcher.add_handler(CommandHandler("help", help_command))

#     # on non command i.e message - echo the message on Telegram
#     dispatcher.add_handler(MessageHandler(
#         Filters.text & ~Filters.command, echo))

#     # Start the Bot
#     updater.start_polling()

#     # Run the bot until you press Ctrl-C or the process receives SIGINT,
#     # SIGTERM or SIGABRT. This should be used most of the time, since
#     # start_polling() is non-blocking and will stop the bot gracefully.
#     updater.idle()


# if __name__ == '__main__':
#     main()
