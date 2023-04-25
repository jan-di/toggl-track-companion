from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    Integer,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.models.base import orm_base


class User(orm_base):
    __tablename__ = "app_user"
    id = Column(Integer, primary_key=True, autoincrement=False)
    toggl_user_id = Column(Integer, ForeignKey("toggl_user.id"))
    start = Column(Date)
    enabled = Column(Boolean)
    name = Column(String, nullable=False)
    username = Column(String)
    language_code = Column(String)

    toggl_user = relationship(
        "app.models.toggl.User", back_populates="app_user", uselist=False
    )

    def __init__(self, user_id: int):
        self.id = user_id


class Schedule(orm_base):
    __tablename__ = "app_schedule"
    id = Column(Integer, primary_key=True)
    toggl_user_id = Column(Integer, ForeignKey("toggl_user.id"), nullable=False)
    toggl_workspace_id = Column(
        Integer, ForeignKey("toggl_workspace.id"), nullable=False
    )
    start = Column(Date, nullable=False)
    end = Column(Date)
    day0 = Column(Integer, nullable=False)
    day1 = Column(Integer, nullable=False)
    day2 = Column(Integer, nullable=False)
    day3 = Column(Integer, nullable=False)
    day4 = Column(Integer, nullable=False)
    day5 = Column(Integer, nullable=False)
    day6 = Column(Integer, nullable=False)

    toggl_workspace = relationship("app.models.toggl.Workspace", uselist=False)

    def __repr__(self):
        return f"<Schedule(id='{self.id}')>"


class ScheduleException(orm_base):
    __tablename__ = "app_schedule_exception"
    id = Column(Integer, primary_key=True)
    toggl_user_id = Column(Integer, ForeignKey("toggl_user.id"), nullable=False)
    toggl_workspace_id = Column(
        Integer, ForeignKey("toggl_workspace.id"), nullable=False
    )
    start = Column(Date, nullable=False)
    rrule = Column(String, nullable=False)
    factor = Column(Float, nullable=False, default=1.0)
    addend = Column(Integer, nullable=False, default=0)
    description = Column(String)

    toggl_workspace = relationship("app.models.toggl.Workspace", uselist=False)

    def __repr__(self):
        return f"<ScheduleException(id='{self.id}')>"