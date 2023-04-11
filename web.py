#!/usr/bin/env python

import logging

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.web.flask import FlaskApp


def main() -> None:
    Log()
    config = Config()
    database = Database(config.database_uri)

    logging.info("Starting web..")

    app = FlaskApp(config.server_name, config.session_secret)

    app.run()

    database.disconnect()
    logging.info("Exiting web..")


if __name__ == "__main__":
    main()
