from os import path

from flask import Flask
from src.web import FlaskApp
from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
import version

Log.init()
logger = Log.get_logger("root")
logger.info("Start web_prod @%s (%s)", version.VERSION, version.COMMIT)

script_dir = path.dirname(path.realpath(__file__))
config = Config(path.join(script_dir, ".env"))
logger.setLevel(config.log_level)


def get_app() -> Flask:
    Database.connect(config.database_uri)

    app = FlaskApp(config.flask_session_secret, script_dir)

    return app.app


def worker_exit(_server, _worker):
    Database.disconnect()


def on_exit(_server) -> None:
    logger.info("Exit web_prod")
