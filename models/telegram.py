""" Telegram Models """

from sqlalchemy import Boolean, Column, Integer, String
from util import Database


class User(Database.Base):
    """
    Representation of a Telegram User

    See also https://core.telegram.org/bots/api#user
    """

    __tablename__ = "telegram_user"
    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    username = Column(String)
    language_code = Column(String)
    is_premium = Column(Boolean)

    @classmethod
    def create_from_data(cls: 'User', data: map) -> 'User':
        """ Creates a new TelegramUser Object based on an API response """

        return User(
            id=data['id'],
            firstname=data['first_name'],
            lastname=data['last_name'],
            username=data['username'],
            language_code=data['language_code'],
            is_premium=data['is_premium'] or False
        )

    def __repr__(self):
        return f"<telegram.User(id='{self.id}')>"
