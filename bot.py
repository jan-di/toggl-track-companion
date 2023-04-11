#!/usr/bin/env python

import logging

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.telegram.bot import TelegramBot


def main() -> None:
    Log()
    config = Config()
    database = Database(config.database_uri)

    logging.info("Starting bot..")

    bot = TelegramBot(config.telegram_token, database)

    bot.set_my_commands()
    bot.start()

    database.disconnect()
    logging.info("Exiting bot..")


if __name__ == "__main__":
    main()
