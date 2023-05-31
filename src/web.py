from os import path
from functools import wraps
from datetime import datetime
from flask import Flask, session, request, redirect, render_template, url_for
from httpx import HTTPStatusError

from src.toggl import TogglApi, TogglUpdater
from src.db.schema import User, Workspace


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

                try:
                    user_data = toggl_api.get_me()

                    session["user_id"] = user_data["id"]
                    next_url = request.args.get("next", url_for("index"))

                    toggl_updater.create_or_update_user_from_api(user_data)

                    return redirect(next_url)
                except HTTPStatusError:
                    error_msg = "Login failed."

            return render_template("login.html.j2", error_msg=error_msg)

        @self.app.route("/logout")
        @self.__require_auth
        def logout():
            del session["user_id"]
            return redirect("login")

        @self.app.route("/profile", methods=["GET", "POST"])
        @self.__require_auth
        def profile():
            user = User.objects.get(user_id=session["user_id"])

            if request.method == "POST":
                for key, value in request.form.items():
                    workspace_id, name = key.split("-", 1)

                    workspace = Workspace.objects.get(workspace_id=workspace_id)
                    user_workspace = user.workspaces.get(workspace=workspace)

                    match name:
                        case "start-of-aggregation":
                            user_workspace.start_of_aggregation = datetime.strptime(
                                value, "%Y-%m-%d"
                            ).date()
                        case "schedule-calendar-url":
                            user_workspace.schedule_calendar_url = value

                    user.save()

            return render_template(
                "profile.html.j2", user=user, toggl_api_class=TogglApi
            )

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
