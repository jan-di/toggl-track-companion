from os import path
from functools import wraps
from datetime import datetime, date, timezone
from flask import Flask, session, request, redirect, render_template, url_for
from httpx import HTTPStatusError
import humanize
import pytz
import json

import version
from src.toggl import TogglApi, TogglUpdater
from src.db.schema import User, Workspace
from src.schedule import Resolver, CalendarSync


class FlaskApp:
    def __init__(self, session_secret: str, root_dir: str):
        self.app = Flask(
            __name__,
            static_folder=path.join(root_dir, "static"),
            template_folder=path.join(root_dir, "template"),
        )
        self.app.config.update(SECRET_KEY=session_secret)

        @self.app.route("/")
        @self.__require_auth
        def index():
            user = User.objects.get(user_id=session["user_id"])

            return render_template("index.html.j2", user=user)

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
                    session["user_name"] = user_data["fullname"]
                    next_url = request.args.get("next", url_for("index"))

                    toggl_updater.create_or_update_user_from_api(user_data)

                    return redirect(next_url)
                except HTTPStatusError:
                    error_msg = "Login failed."

            return render_template("login.html.j2", error_msg=error_msg)

        @self.app.route("/webhook", methods=["POST"])
        def webhook():
            event = request.json

            response = {}
            if "validation_code" in event:
                response["validation_code"] = event["validation_code"]

            return response, 200

        @self.app.route("/logout", methods=["POST"])
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
                            if len(value) > 0:
                                user_workspace.start_of_aggregation = datetime.strptime(
                                    value, "%Y-%m-%d"
                                ).date()
                        case "schedule-calendar-url":
                            user_workspace.schedule_calendar_url = (
                                value if len(value) > 1 else None
                            )

                    cal_sync = CalendarSync()
                    user = cal_sync.update_user(user, 0)

            return render_template(
                "profile.html.j2", user=user, toggl_api_class=TogglApi
            )

        @self.app.route("/detailed-report/<workspace_id>")
        @self.__require_auth
        def report(workspace_id):
            user = User.objects.get(user_id=session["user_id"])

            workspace = Workspace.objects.get(workspace_id=workspace_id)
            user_workspace = user.workspaces.get(workspace=workspace)

            report = Resolver.create_report(
                user, workspace, user_workspace.start_of_aggregation, date.today()
            )

            return render_template("detailed_report.html.j2", user=user, report=report)

        @self.app.template_filter()
        def format_number(number: int):
            if number == 0:
                return f'<span class="text-muted">{number}</span>'
            else:
                return f"<span>{number}</span>"

        @self.app.template_filter()
        def format_percentage(number: float, precision: int = 2):
            if number is None:
                return "---%"
            return f"{round(float(number) * 100, precision)}%"

        @self.app.template_filter()
        def format_time(total_seconds: int):
            minutes, seconds = divmod(abs(total_seconds), 60)
            hours, minutes = divmod(minutes, 60)

            result = f"{hours:02}:{minutes:02}:{seconds:02}"
            muted_length = len(result) - len(result.lstrip(":0"))
            if muted_length > 0:
                result = f'<span class="text-muted">{result[:muted_length]}</span>{result[muted_length:]}'
            return f'{"-" if total_seconds < 0 else "&nbsp;"}{result}'

        @self.app.template_filter()
        def format_datetime(input_dt: datetime):
            return input_dt.strftime("%Y-%m-%d %H:%M:%S")

        @self.app.template_filter()
        def format_weekday(weekday: int, length: int = None):
            weekdays = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            return weekdays[weekday][:length]

        @self.app.template_filter()
        def as_timezone(input_dt: datetime, timezone_str: str):
            return input_dt.astimezone(pytz.timezone(timezone_str))

        @self.app.context_processor
        def inject_now():
            return {"now": datetime.now(timezone.utc)}

        @self.app.context_processor
        def inject_version():
            return {"version": version}

        @self.app.context_processor
        def inject_humanize():
            return {"humanize": humanize}

    def run_debug(self):
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
