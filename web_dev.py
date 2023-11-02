#!/usr/bin/env python

from os import path

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.web.factory import FlaskFactory
import version


def main() -> None:
    Log.init()
    logger = Log.get_logger("root")
    logger.info("Start web_dev @%s (%s)", version.VERSION, version.COMMIT)

    script_dir = path.dirname(path.realpath(__file__))
    config = Config(path.join(script_dir, ".env"))
    logger.setLevel(config.log_level)
    Database.connect(config.database_uri)

    app = FlaskFactory.create_app(config.flask_session_secret, script_dir)
    app.run(debug=True, use_reloader=False, host="0.0.0.0")

    Database.disconnect()
    logger.info("Exit web_dev")


if __name__ == "__main__":
    main()
