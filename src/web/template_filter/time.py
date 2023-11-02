from datetime import datetime
import pytz


class Time:
    @staticmethod
    def as_timezone(input_dt: datetime, timezone_str: str):
        return input_dt.astimezone(pytz.timezone(timezone_str))
