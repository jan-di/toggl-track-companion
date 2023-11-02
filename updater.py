#!/usr/bin/env python

from os import path

from src.web.factory import FlaskFactory
from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.updater import Updater
import version


def main():
    Log.init()
    logger = Log.get_logger("root")
    logger.info("Start updater @%s (%s)", version.VERSION, version.COMMIT)

    script_dir = path.dirname(path.realpath(__file__))
    config = Config(path.join(script_dir, ".env"))
    logger.setLevel(config.log_level)
    Database.connect(config.database_uri)

    web_app = FlaskFactory.create_app(
        config.flask_session_secret,
        script_dir,
        config.server_url,
    )
    updater = Updater(
        config.sync_interval_calendar,
        config.sync_interval_toggl,
        web_app,
        config.server_id,
    )
    updater.run()

    Database.disconnect()
    logger.info("Exit updater")


if __name__ == "__main__":
    main()
