import logging
from mongoengine import connect, disconnect


class Database:
    @staticmethod
    def connect(uri: str):
        connect(host=uri)
        logging.debug("Connected to database %s", uri)

    @staticmethod
    def disconnect():
        disconnect()
        logging.debug("Disconnected database")
