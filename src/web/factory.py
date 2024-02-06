from os import path
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, session, request, redirect, url_for
import humanize
from urllib.parse import urlparse

import version
from src.util.log import Log
from src.web import controller, template_filter


class FlaskFactory:
    @classmethod
    def create_app(
        cls, session_secret: str, root_dir: str, server_url: str = None
    ) -> Flask:
        app = Flask(
            __name__,
            static_folder=path.join(root_dir, "static"),
            template_folder=path.join(root_dir, "template"),
        )
        app.config.update(SECRET_KEY=session_secret)
        if server_url is not None:
            url_parts = urlparse(server_url)
            app.config.update(
                SERVER_NAME=url_parts.netloc,
                APPLICATION_ROOT=url_parts.path,
                PREFERRED_URL_SCHEME=url_parts.scheme,
            )

        # Create controllers
        index_controller = controller.Index()
        security_controller = controller.Security()
        webhook_logger = Log.get_logger("webhook")
        webhook_controller = controller.Webhook(webhook_logger)
        profile_controller = controller.Profile()
        report_controller = controller.Report()

        # Add routes
        @app.route("/")
        @cls.__require_auth
        def index():
            return index_controller.index()

        @app.route("/login", methods=["GET", "POST"])
        def login():
            return security_controller.login()

        @app.route("/logout", methods=["POST"])
        @cls.__require_auth
        def logout():
            return security_controller.logout()

        @app.route("/webhook/<int:workspace_id>/<int:user_id>", methods=["POST"])
        def webhook(workspace_id: int, user_id: int):
            return webhook_controller.process(workspace_id, user_id)

        @app.route("/profile", methods=["GET", "POST"])
        @cls.__require_auth
        def profile():
            return profile_controller.profile()

        @app.route("/stats/<int:workspace_id>")
        @cls.__require_auth
        def stats(workspace_id: int):
            return report_controller.stats(workspace_id)

        @app.route("/detailed-report/<int:workspace_id>")
        @cls.__require_auth
        def report(workspace_id: int):
            return report_controller.detailed(workspace_id)

        # Add template filters
        app.add_template_filter(template_filter.Formatting.format_percentage)
        app.add_template_filter(template_filter.Formatting.format_number)
        app.add_template_filter(template_filter.Formatting.format_number)
        app.add_template_filter(template_filter.Formatting.format_time)
        app.add_template_filter(template_filter.Formatting.format_datetime)
        app.add_template_filter(template_filter.Formatting.format_weekday)
        app.add_template_filter(template_filter.Time.as_timezone)

        # Add context processors
        @app.context_processor
        def inject_context_processors():
            return {
                "now": datetime.now(timezone.utc),
                "version": version,
                "humanize": humanize,
            }

        return app

    @classmethod
    def __require_auth(cls, func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session or session["user_id"] is None:
                return redirect(url_for("login", next=request.path))
            return func(*args, **kwargs)

        return decorated_function
