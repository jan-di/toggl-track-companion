""" Toggl Models """

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, BigInteger
from util import Database


class User(Database.Base):
    """
    Representation of a Toggl user

    See also https://developers.track.toggl.com/docs/api/me#get-me
    """

    __tablename__ = "toggl_user"
    id = Column(Integer, primary_key=True)
    fullname = Column(String)
    email = Column(String)
    country_id = Column(Integer)
    timezone = Column(String)
    beginning_of_week = Column(Integer)
    image_url = Column(String)
    created_at = Column(DateTime)
    api_token = Column(String)

    @classmethod
    def create_from_data(cls: 'User', data: map) -> 'User':
        """ Creates a new User Object based on an API response """

        return User(
            id=data['id'],
            fullname=data['fullname'],
            email=data['email'],
            country_id=data['country_id'],
            timezone=data['timezone'],
            beginning_of_week=data['beginning_of_week'],
            image_url=data['image_url'],
            created_at=data['created_at'],
            api_token=data['api_token'],
        )

    def __repr__(self):
        return f"<toggl.User(id='{self.id}')>"


class TimeEntry(Database.Base):
    """
    Representation of a Toggl TimeEntry

    See also https://developers.track.toggl.com/docs/api/time_entries#get-timeentries
    """
    __tablename__ = "toggl_time_entry"
    id = Column(BigInteger, primary_key=True)
    description = Column(String)
    start = Column(DateTime)
    stop = Column(DateTime)
    user_id = Column(Integer, ForeignKey("toggl_user.id"))

    @classmethod
    def create_from_data(cls: 'TimeEntry', data: map) -> 'TimeEntry':
        """ Creates a new TimeEntry Object based on an API response """

        return TimeEntry(
            id=data['id'],
            description=data['description'],
            start=data['start'],
            stop=data['stop'],
            user_id=data['user_id'],
        )

    def __repr__(self):
        return f"<toggl.TimeEntry(id='{self.id}')>"
