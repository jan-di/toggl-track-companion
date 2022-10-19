from flask import Flask, request
from app import telegram
from app.util import Config


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config.update(SERVER_NAME=config.server_name, SECRET_KEY=config.session_secret)

    @app.route("/auth")
    def auth():
        result = ""
        result += f"{telegram.validate_web_auth(config.telegram_token, request.args.to_dict())}"

        return result

    return app
