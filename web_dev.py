#!/usr/bin/env python

from os import path

from src.web import FlaskApp
from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
import version


def main() -> None:
    Log.init()
    logger = Log.get_logger("root")
    logger.info("Start web_dev @%s (%s)", version.VERSION, version.COMMIT)

    script_dir = path.dirname(path.realpath(__file__))
    config = Config(path.join(script_dir, ".env"))
    logger.setLevel(config.log_level)
    Database.connect(config.database_uri)

    app = FlaskApp(config.flask_session_secret, script_dir)
    app.run_debug()

    Database.disconnect()
    logger.info("Exit web_dev")


if __name__ == "__main__":
    main()
