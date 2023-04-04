import httpx
from icalendar import Calendar
from src.db.schema import User

class CalendarSync:
    def get_users_to_sync(self) -> User:
        return User.objects()

    def sync_calendar(self, calendar: Calendar) -> None:
        ical = self._fetch_calendar(calendar.url)

    def _fetch_calendar(self, url: str) -> Calendar:
        ics = httpx.get(url, timeout=20)

        calendar = Calendar.from_ical(ics.content)
        return calendar