from datetime import date
import decimal
from functools import wraps
from flask import Flask, request, session, redirect, render_template
from app import telegram
from app.models.app import Schedule, ScheduleException, User
from app.toggl.api import Api
from app.util import Config, Database
from app.report import analyzer


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session["user_id"] is None:
            return "not authenticated", 401
        return f(*args, **kwargs)

    return decorated_function


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config.update(SERVER_NAME=config.server_name, SECRET_KEY=config.session_secret)

    database = Database(config.database_uri)

    @app.route("/auth")
    def auth():
        auth_valid = telegram.validate_web_auth(
            config.telegram_token, request.args.to_dict()
        )
        if auth_valid:
            session["user_id"] = request.args["id"]
        else:
            return "authentication invalid", 401

        return redirect(request.args["_next"], code=302)

    @app.route("/connect", methods=["POST", "GET"])
    @require_auth
    def connect():
        if request.method == "GET":
            return render_template("index.html.j2")

        elif request.method == "POST":

            toggl_api = Api(request.form.get("apitoken"))
            toggl_user = toggl_api.get_me()

            if toggl_user is not None:
                with database.get_session() as db:

                    db.merge(toggl_user)

                    user = db.query(User).get(session["user_id"])
                    user.toggl_user_id = toggl_user.id
                    user.start = date.today()
                    user.enabled = True

                    db.commit()
                    db.flush()

                return "success. you can return to telegram now."

            # will never be reached, as request will crash lol
            return "api token invalid"

    @app.route("/preferences", methods=["POST", "GET"])
    @require_auth
    def preferences():

        with database.get_session() as db:

            user = db.query(User).get(session["user_id"])
            if user.toggl_user is not None:
                schedules = db.query(Schedule).filter(
                    Schedule.toggl_user_id == user.toggl_user.id
                )
                schedule_exceptions = db.query(ScheduleException).filter(
                    ScheduleException.toggl_user_id == user.toggl_user.id
                )
            else:
                schedules = []
                schedule_exceptions = []

        return render_template(
            "config.html.j2",
            schedules=schedules,
            schedule_exceptions=schedule_exceptions,
        )

    @app.route("/report", methods=["POST", "GET"])
    @require_auth
    def report():

        with database.get_session() as db:

            user = db.query(User).get(session["user_id"])
            if user.toggl_user is not None:

                text_report, report = analyzer.analyze(
                    session=db, user=user, toggl_user=user.toggl_user
                )

                return render_template(
                    "report.html.j2", text_report=text_report, report=report
                )
            else:
                return "lol"

    @app.template_filter()
    def format_percentage(number: float, precision: int = 2):
        if number is None:
            return "---%"
        return f"{round(float(number) * 100, precision)}%"

    @app.template_filter()
    def format_time(total_seconds: int):
        minutes, seconds = divmod(abs(total_seconds), 60)
        hours, minutes = divmod(minutes, 60)

        result = f"{hours:02}:{minutes:02}:{seconds:02}"
        muted_length = len(result) - len(result.lstrip(":0"))
        if muted_length > 0:
            result = f'{"-" if total_seconds < 0 else ""}<span class="text-muted">{result[:muted_length]}</span>{result[muted_length:]}'
        return result

    return app
