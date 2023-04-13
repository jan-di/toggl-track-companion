import hashlib
import hmac
from os import path
from functools import wraps
from flask import Flask, session, request, redirect, render_template, url_for

from src.db.schema import User
from src.toggl import TogglApi


class FlaskApp:
    def __init__(
        self, server_name: str, session_secret: str, root_dir: str, telegram_token: str
    ):
        app = Flask(
            __name__,
            static_folder=path.join(root_dir, "static"),
            template_folder=path.join(root_dir, "template"),
        )
        app.config.update(SERVER_NAME=server_name, SECRET_KEY=session_secret)

        @app.route("/health")
        def route_health():
            return "ok", 200

        @app.route("/login")
        def route_login():
            return render_template("login.html.j2")

        @app.route("/logout")
        def route_logout():
            session.clear()
            return "ok", 200

        @app.route("/connect", methods=["POST", "GET"])
        @self.require_auth
        def route_connect():
            if request.method == "GET":
                return render_template("connect.html.j2")

            elif request.method == "POST":
                toggl_api = TogglApi(request.form.get("apitoken"))
                success, toggl_user = toggl_api.get_me()

                if not success:
                    return "api token invalid", 400
                else:
                    user = User.objects.get(telegram_id=session["user_id"])

                    user.toggl_id = toggl_user["id"]
                    user.toggl_name = toggl_user["fullname"]
                    user.toggl_image_url = toggl_user["image_url"]

                    user.save()

                    return "toggl account connected"

        @app.route("/auth")
        def route_auth():
            auth_valid = self.validate_web_auth(
                self.telegram_token, request.args.to_dict()
            )
            if auth_valid:
                session["user_id"] = request.args["id"]
            else:
                return "authentication invalid", 401

            return redirect(request.args["_next"], code=302)

        @app.route("/profile")
        @self.require_auth
        def route_profile():
            user = User.objects.get(telegram_id=session["user_id"])

            return render_template("profile.html.j2", user=user)

        self.app = app
        self.telegram_token = telegram_token

    def run(self):
        self.app.run(
            debug=True, ssl_context="adhoc", use_reloader=False, host="0.0.0.0"
        )

    def get_context(self):
        return self.app.app_context()

    def require_auth(self, func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session or session["user_id"] is None:
                return (
                    f'not authenticated. <a href="{ url_for("route_login")}">login</a>',
                    401,
                )
            return func(*args, **kwargs)

        return decorated_function

    def validate_web_auth(self, token: str, params: dict[str]) -> bool:
        params = params.copy()
        token_hash = hashlib.sha256(str.encode(token)).digest()
        check_hash = params["hash"]

        for k in list(params.keys()):
            if k.startswith("_"):
                del params[k]

        params.pop("hash")

        compare_string = "\n".join(
            map(lambda key: f"{key}={params[key]}", sorted(params))
        )
        compare_hash = hmac.new(
            token_hash, str.encode(compare_string), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(check_hash, compare_hash)
