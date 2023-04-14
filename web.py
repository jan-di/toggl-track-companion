#!/usr/bin/env python

from os import path

from src.web import FlaskApp
from src.util.config import Config
from src.util.log import Log


def main() -> None:
    Log.init()
    logger = Log.get_logger("root")
    logger.info("Starting web..")

    script_dir = path.dirname(path.realpath(__file__))
    config = Config(path.join(script_dir, ".env"))

    app = FlaskApp(config.server_name, config.session_secret, script_dir)
    app.run()

    logger.info("Exiting web..")


if __name__ == "__main__":
    main()
