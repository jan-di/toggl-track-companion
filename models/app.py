from sqlalchemy import Column, DateTime, Integer, ForeignKey
from util import Database


class WorkSchedule(Database.Base):
    __tablename__ = "app_work_schedule"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("toggl_user.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("toggl_workspace.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime)
    day0 = Column(Integer, nullable=False)
    day1 = Column(Integer, nullable=False)
    day2 = Column(Integer, nullable=False)
    day3 = Column(Integer, nullable=False)
    day4 = Column(Integer, nullable=False)
    day5 = Column(Integer, nullable=False)
    day6 = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<WorkSchedule(id='{self.id}')>"
