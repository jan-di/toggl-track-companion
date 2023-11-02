from flask import Response, render_template, session

from src.db.entity.user import User


class Index:
    def index(self) -> Response | str:
        user = User.objects.get(user_id=session["user_id"])

        return render_template("index.html.j2", user=user)
