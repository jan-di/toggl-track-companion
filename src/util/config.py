import os

from dotenv import dotenv_values


class Config:
    def __init__(self, dotenv_file: str = ".env"):
        values = {
            **dotenv_values(dotenv_file),
            **os.environ,
        }

        self.database_uri = values.get("DATABASE_URI")
        self.server_name = values.get("SERVER_NAME")
        self.session_secret = values.get("SESSION_SECRET")
        self.sync_interval = int(values.get("SYNC_INTERVAL", 86400))
