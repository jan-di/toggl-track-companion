#!/usr/bin/env python

from os import path

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.updater import Updater


def main():
    Log.init()
    logger = Log.get_logger("root")
    logger.info("Starting updater..")

    script_dir = path.dirname(path.realpath(__file__))
    config = Config(path.join(script_dir, ".env"))
    Database.connect(config.database_uri)

    updater = Updater(config.sync_interval_calendar, config.sync_interval_toggl)
    updater.run()

    Database.disconnect()
    logger.info("Exiting updater..")


if __name__ == "__main__":
    main()
