from flask import Response, request, session, url_for, render_template, redirect
from httpx import HTTPStatusError

from src.toggl.api import TogglApi
from src.db.entity import User


class Security:
    def login(self) -> Response | str:
        error_msg = None
        if "user_id" in session and session["user_id"]:
            return redirect(url_for("index"))
        elif request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            toggl_api = TogglApi(username=username, password=password)

            try:
                user_data = toggl_api.get_me()

                session["user_id"] = user_data.id
                session["user_name"] = user_data.fullname
                next_url = request.args.get("next", url_for("index"))

                User.create_or_update_via_api_data(user_data)

                return redirect(next_url)
            except HTTPStatusError:
                error_msg = "Login failed."

        return render_template("login.html.j2", error_msg=error_msg)

    def logout(self) -> Response | str:
        del session["user_id"]

        return redirect("login")
