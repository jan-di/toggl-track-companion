import logging
from mongoengine import connect, disconnect
from mongoengine.connection import get_db
from urllib.parse import urlparse


class Database:
    @staticmethod
    def sanitize_url(url: str):
        parsed = urlparse(url)

        netloc = ""
        if parsed.username is not None and len(parsed.username) > 0:
            netloc += f"{parsed.username}:"
            if parsed.password is not None and len(parsed.password) > 0:
                netloc += "****"
            netloc += "@"
        netloc += parsed.hostname

        replaced = parsed._replace(netloc=netloc)
        return replaced.geturl()

    @staticmethod
    def connect(url: str):
        connect(host=url, tz_aware=True)

        mongodb = get_db()
        status = mongodb.command("serverStatus")

        logging.debug(
            "Connected to database %s, version %s",
            Database.sanitize_url(url),
            status["version"],
        )

    @staticmethod
    def disconnect():
        disconnect()
        logging.debug("Disconnected database")
