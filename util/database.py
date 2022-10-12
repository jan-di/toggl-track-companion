""" Database Utilities """

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:
    """ Database Utilities """

    Base = declarative_base()

    def __init__(self, database_uri):
        self.engine = create_engine(database_uri)
        self.__session_maker = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.__session_maker()
