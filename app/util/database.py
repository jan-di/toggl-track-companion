from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import orm_base

# pylint: disable=unused-import
import app.models.toggl
import app.models.app


class Database:
    orm_base = orm_base

    def __init__(self, database_uri):
        self.engine = create_engine(database_uri)
        self.__session_maker = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.__session_maker()
