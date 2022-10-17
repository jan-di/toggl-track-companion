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
from util import Database


class User(Database.Base):
    __tablename__ = "app_user"
    id = Column(Integer, primary_key=True)
    toggl_user_id = Column(Integer, ForeignKey("toggl_user.id"), nullable=False)
    start = Column(Date, nullable=False)
    disabled = Column(Boolean, nullable=False)

    toggl_user = relationship(
        "models.toggl.User", back_populates="app_user", uselist=False
    )


class Schedule(Database.Base):
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

    def __repr__(self):
        return f"<Schedule(id='{self.id}')>"


class ScheduleException(Database.Base):
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

    def __repr__(self):
        return f"<ScheduleException(id='{self.id}')>"
