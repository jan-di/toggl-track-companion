from datetime import date
from sqlalchemy.orm import Session
from models.app import ScheduleException, Schedule
from models.toggl import User, Workspace


class ScheduleRepository:
    def __init__(self, session: Session):
        self.session = session
        self.entity = Schedule

    def get_by_date_range(
        self,
        toggl_user: User,
        toggl_workspace: Workspace,
        start: date,
        end: date,
    ):
        return list(
            self.session.query(Schedule).filter(
                (Schedule.toggl_user_id == toggl_user.id)
                & (Schedule.toggl_workspace_id == toggl_workspace.id)
                & (
                    (Schedule.start >= start) & (Schedule.start <= end)
                    | (Schedule.end >= start) & (Schedule.end <= end)
                    | (Schedule.start < start) & (Schedule.end > end)
                    | (Schedule.start <= end) & (Schedule.end.is_(None))
                )
            )
        )


class ScheduleExceptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_user_and_workspace(
        self,
        toggl_user: User,
        toggl_workspace: Workspace,
    ):
        return list(
            self.session.query(ScheduleException).filter(
                (ScheduleException.toggl_user_id == toggl_user.id)
                & (ScheduleException.toggl_workspace_id == toggl_workspace.id)
            )
        )
