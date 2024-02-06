from flask import Response, request, session, render_template
from datetime import datetime

from src.toggl.api import TogglApi
from src.db.entity import Workspace, User
from src.schedule import CalendarSync


class Profile:
    def profile(self) -> Response | str:
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

        return render_template("profile.html.j2", user=user, toggl_api_class=TogglApi)
