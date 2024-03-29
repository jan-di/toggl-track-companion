import os

from dotenv import dotenv_values


class Config:
    def __init__(self, dotenv_file: str = ".env"):
        values = {
            **dotenv_values(dotenv_file),
            **os.environ,
        }

        self.server_id = values.get("SERVER_ID")
        self.server_url = values.get("SERVER_URL")
        self.database_uri = values.get("DATABASE_URI")
        self.flask_session_secret = values.get("FLASK_SESSION_SECRET")
        self.sync_interval_calendar = int(values.get("SYNC_INTERVAL_CALENDAR", 3600))
        self.sync_interval_toggl = int(values.get("SYNC_INTERVAL_TOGGL", 86400))
        self.log_level = values.get("LOG_LEVEL", "INFO")

        if self.server_id is None:
            raise RuntimeError("Missing config SERVER_ID")
