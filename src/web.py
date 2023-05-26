from os import path
from functools import wraps
from flask import Flask, session, request, redirect, render_template, url_for

from src.toggl import TogglApi, TogglUpdater
from src.db.schema import User
from mongoengine import DoesNotExist


class FlaskApp:
    def __init__(self, server_name: str, session_secret: str, root_dir: str):
        self.app = Flask(
            __name__,
            static_folder=path.join(root_dir, "static"),
            template_folder=path.join(root_dir, "template"),
        )
        self.app.config.update(SERVER_NAME=server_name, SECRET_KEY=session_secret)

        @self.app.route("/")
        @self.__require_auth
        def index():
            return render_template("index.html.j2")

        @self.app.route("/login", methods=["GET", "POST"])
        def login():
            error_msg = None
            if request.method == "POST":
                username = request.form["username"]
                password = request.form["password"]

                toggl_api = TogglApi(username=username, password=password)
                toggl_updater = TogglUpdater()
                success, toggl_user = toggl_api.get_me()

                if success:
                    session["user_id"] = toggl_user["id"]
                    next_url = request.args.get("next", url_for("index"))

                    toggl_updater.create_or_update_user(toggl_user)

                    return redirect(next_url)
                else:
                    error_msg = "Login failed."

            return render_template("login.html.j2", error_msg=error_msg)

        @self.app.route("/logout")
        @self.__require_auth
        def logout():
            del session["user_id"]
            return redirect("login")

        @self.app.route("/profile")
        @self.__require_auth
        def profile():
            user = User.objects.get(user_id=session["user_id"])

            return render_template("profile.html.j2", user=user)

    def run(self):
        self.app.run(debug=True, use_reloader=False, host="0.0.0.0")

    def get_context(self):
        return self.app.app_context()

    def __require_auth(self, func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session or session["user_id"] is None:
                return redirect(url_for("login", next=request.path))
            return func(*args, **kwargs)

        return decorated_function
