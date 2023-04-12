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
from src.db.schema import User


class TelegramBot:
    def __init__(self, token: str, flask_app: FlaskApp, database: Database):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler("start", self._start_command))
        self.dispatcher.add_handler(CommandHandler("profile", self._profile_command))
        self.dispatcher.add_handler(CommandHandler("connect", self._connect_command))
        self.dispatcher.add_handler(
            CommandHandler("disconnect", self._disconnect_command)
        )
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
                BotCommand("/connect", "Connect with a toggl track account"),
                BotCommand("/disconnect", "Disconnect toggl track account"),
            ],
        )

    def start(self) -> None:
        self.updater.start_polling()
        self.updater.idle()

    def _start_command(self, update: Update, _context: CallbackContext) -> None:
        user = update.effective_user
        update.message.reply_markdown_v2(rf"Hi {user.mention_markdown_v2()}\!")

    def _profile_command(self, update: Update, context: CallbackContext) -> None:
        user = self._create_or_update_user(update.effective_user)

        reply_markup = self._create_auth_reply_markup(
            context, "Open user profile", "profile"
        )
        update.message.reply_text("Open user profile", reply_markup=reply_markup)

    def _connect_command(self, update: Update, context: CallbackContext) -> None:
        reply_markup = self._create_auth_reply_markup(
            context, "Connect with Toggl Track", "connect"
        )
        update.message.reply_text(
            "To connect with your toggl track account, open the connection wizard.",
            reply_markup=reply_markup,
        )

    def _disconnect_command(self, update: Update, context: CallbackContext) -> None:
        pass

    def _create_or_update_user(self, sender: dict) -> User:
        user = User.objects.get(telegram_id=sender.id)

        if not user:
            user = User()
            user.telegram_id = sender.id

        user.telegram_name = f"{sender['first_name']} {sender['last_name'] if sender['last_name'] is not None else '' }".strip()
        user.telegram_username = sender["username"]

        user.save()

        return user

    def _create_auth_reply_markup(
        self, context: CallbackContext, button_text: str, next_url: str
    ):
        with context.bot_data["flask"].get_context():
            login_url = LoginUrl(url_for("route_auth", _scheme="https", _next=next_url))
        keyboard = [
            [
                InlineKeyboardButton(button_text, login_url=login_url),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
