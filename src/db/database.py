import logging
from mongoengine import connect, disconnect


class Database:
    def __init__(self, uri: str, auto_connect: bool = True):
        self.uri = uri
        if auto_connect:
            self.connect()

    def connect(self):
        connect(host=self.uri)
        logging.debug("Connected to database %s", self.uri)

    def disconnect(self):
        disconnect()
