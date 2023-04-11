from flask import url_for
from telegram import (
    BotCommand,
    LoginUrl,
    # ParseMode,
    Update,
    # ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    # MessageHandler,
    # Filters,
    CallbackContext,
)

from src.db.database import Database
from src.web import FlaskApp


class TelegramBot:
    def __init__(self, token: str, flask_app: FlaskApp, database: Database):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler("start", self._start_command))
        self.dispatcher.add_handler(CommandHandler("profile", self._profile_command))
        # dispatcher.add_handler(CommandHandler("disconnect", disconnect_command))
        # dispatcher.add_handler(CommandHandler("fetch", fetch_command))
        # dispatcher.add_handler(CommandHandler("analyze", analyze_command))
        # dispatcher.add_handler(CommandHandler("preferences", preferences_command))
        # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

        self.dispatcher.bot_data["flask"] = flask_app
        self.dispatcher.bot_data["database"] = database

        self.bot = self.updater.bot

    def set_my_commands(self) -> None:
        self.bot.set_my_commands(
            commands=[
                BotCommand("/profile", "Open your profile page"),
            ],
        )

    def start(self) -> None:
        self.updater.start_polling()
        self.updater.idle()

    def _start_command(self, update: Update, _context: CallbackContext) -> None:
        user = update.effective_user
        update.message.reply_markdown_v2(rf"Hi {user.mention_markdown_v2()}\!")

    def _profile_command(self, update: Update, context: CallbackContext) -> None:
        with context.bot_data["flask"].get_context():
            login_url = LoginUrl(
                url_for("route_auth", _scheme="https", _next="profile")
            )
        keyboard = [
            [
                InlineKeyboardButton("Open profile page", login_url=login_url),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Open user profile", reply_markup=reply_markup)
