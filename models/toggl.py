from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, BigInteger, Table
from sqlalchemy.orm import relationship
from util import Database

toggl_organization_member = Table(
    "toggl_organization_member",
    Database.Base.metadata,
    Column("organization_id", ForeignKey("toggl_organization.id"), primary_key=True),
    Column("user_id", ForeignKey("toggl_user.id"), primary_key=True),
)


class User(Database.Base):
    __tablename__ = "toggl_user"
    id = Column(Integer, primary_key=True, autoincrement=False)
    fullname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    country_id = Column(Integer, nullable=False)
    timezone = Column(String, nullable=False)
    beginning_of_week = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    api_token = Column(String, nullable=False)

    app_user = relationship(
        "models.app.User", back_populates="toggl_user", uselist=False
    )
    organizations = relationship(
        "models.toggl.Organization",
        secondary=toggl_organization_member,
        back_populates="members",
    )
    time_entries = relationship("models.toggl.TimeEntry", back_populates="user")

    def __repr__(self):
        return f"<User(id='{self.id}')>"


class Organization(Database.Base):
    __tablename__ = "toggl_organization"
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime)

    members = relationship(
        "models.toggl.User",
        secondary=toggl_organization_member,
        back_populates="organizations",
    )
    workspaces = relationship("models.toggl.Workspace", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id='{self.id}';name='{self.name}')>"


class Workspace(Database.Base):
    __tablename__ = "toggl_workspace"
    id = Column(Integer, primary_key=True, autoincrement=False)
    organization_id = Column(
        Integer, ForeignKey("toggl_organization.id"), nullable=False
    )
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime)
    logo_url = Column(String, nullable=False)

    organization = relationship(
        "models.toggl.Organization", back_populates="workspaces"
    )
    time_entries = relationship("models.toggl.TimeEntry", back_populates="workspace")

    def __repr__(self):
        return f"<Workspace(id='{self.id}';name='{self.name}')>"


class TimeEntry(Database.Base):
    __tablename__ = "toggl_time_entry"
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    user_id = Column(Integer, ForeignKey("toggl_user.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("toggl_workspace.id"), nullable=False)
    description = Column(String, nullable=False)
    start = Column(DateTime, nullable=False)
    stop = Column(DateTime)
    updated_at = Column(DateTime, nullable=False)
    server_deleted_at = Column(DateTime)

    user = relationship("models.toggl.User", back_populates="time_entries")
    workspace = relationship("models.toggl.Workspace", back_populates="time_entries")

    def __repr__(self):
        return f"<TimeEntry(id='{self.id}')>"
