#!/usr/bin/env python

import logging
from os import path

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.web import FlaskApp


def main() -> None:
    Log()
    config = Config()
    database = Database(config.database_uri)

    logging.info("Starting web..")

    script_dir = path.dirname(path.realpath(__file__))
    app = FlaskApp(config.server_name, config.session_secret, script_dir, config.telegram_token)

    app.run()

    database.disconnect()
    logging.info("Exiting web..")


if __name__ == "__main__":
    main()
