from flask import Response, session, render_template
from datetime import date

from src.db.entity import User, Workspace
from src.schedule import Resolver


class Report:
    def detailed(self, workspace_id: int) -> Response | str:
        user = User.objects.get(user_id=session["user_id"])

        workspace = Workspace.objects.get(workspace_id=workspace_id)
        user_workspace = user.workspaces.get(workspace=workspace)

        report = Resolver.create_report(
            user, workspace, user_workspace.start_of_aggregation, date.today()
        )

        return render_template("detailed_report.html.j2", user=user, report=report)
