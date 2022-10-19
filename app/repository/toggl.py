from datetime import datetime
from sqlalchemy.orm import Session
from app.models.toggl import TimeEntry, User, Workspace


class TimeEntryRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_date_range(
        self,
        toggl_user: User,
        toggl_workspace: Workspace,
        start: datetime,
        end: datetime,
    ):
        return list(
            self.session.query(TimeEntry).filter(
                (TimeEntry.user_id == toggl_user.id)
                & (TimeEntry.workspace_id == toggl_workspace.id)
                & (TimeEntry.start >= start)
                & (TimeEntry.start <= end)
            )
        )
