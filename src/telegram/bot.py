from telegram import (
    # BotCommand,
    # LoginUrl,
    # ParseMode,
    Update,
    # ForceReply,
    # InlineKeyboardButton,
    # InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    # MessageHandler,
    # Filters,
    CallbackContext,
)

from src.db.database import Database


class TelegramBot:
    def __init__(self, token: str, database: Database):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler("start", self._start_command))
        # dispatcher.add_handler(CommandHandler("connect", connect_command))
        # dispatcher.add_handler(CommandHandler("disconnect", disconnect_command))
        # dispatcher.add_handler(CommandHandler("fetch", fetch_command))
        # dispatcher.add_handler(CommandHandler("analyze", analyze_command))
        # dispatcher.add_handler(CommandHandler("preferences", preferences_command))
        # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

        # dispatcher.bot_data["flask"] = flask
        self.dispatcher.bot_data["database"] = database

        self.bot = self.updater.bot

    def set_my_commands(self) -> None:
        pass
        # bot.set_my_commands(
        #     commands=[
        #         BotCommand("/connect", "Connect with your Toggl account"),
        #         BotCommand("/disconnect", "Disconnect from your Toggl account"),
        #         BotCommand("/fetch", "Fetch new resources from toggl"),
        #         BotCommand("/analyze", "Analyze time entries"),
        #         BotCommand("/preferences", "User preferences"),
        #     ],
        # )

    def start(self) -> None:
        self.updater.start_polling()
        self.updater.idle()

    def _start_command(self, update: Update, _context: CallbackContext) -> None:
        user = update.effective_user
        update.message.reply_markdown_v2(rf"Hi {user.mention_markdown_v2()}\!")
