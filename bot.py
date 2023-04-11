#!/usr/bin/env python

import logging
from os import path

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.telegram.bot import TelegramBot
from src.web import FlaskApp


def main() -> None:
    Log()
    config = Config()
    database = Database(config.database_uri)

    logging.info("Starting bot..")

    script_dir = path.dirname(path.realpath(__file__))
    flask_app = FlaskApp(config.server_name, config.session_secret, script_dir, config.telegram_token)
    telegram_bot = TelegramBot(config.telegram_token, flask_app, database)

    telegram_bot.set_my_commands()
    telegram_bot.start()

    database.disconnect()
    logging.info("Exiting bot..")


if __name__ == "__main__":
    main()
