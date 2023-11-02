from datetime import date, datetime, timedelta, timezone
import re
import httpx
from dateutil.rrule import rrulestr
from dateutil.relativedelta import relativedelta
from icalendar import Calendar
from mongoengine import Document
from mongoengine.queryset.visitor import Q
from src.db.entity import User, Workspace, Schedule, Event, TimeEntry


class Day:
    def __init__(self, day_date: date):
        self.date = day_date
        self.schedules = set()
        self.events = set()
        self.time_entry_slices = set()

    @classmethod
    def get_id_by_day(cls, day: date) -> str:
        return day.strftime("%Y-%m-%d")

    def get_id(self) -> str:
        return Day.get_id_by_day(self.date)

    def target_time(self) -> int:
        target_base = sum(map(lambda s: s.target, self.schedules))
        target_mod_relative = 1 + sum(map(lambda e: e.mod_relative, self.events))
        target_mod_absolute = sum(map(lambda e: e.mod_absolute, self.events))

        return int(target_base * target_mod_relative + target_mod_absolute)

    def actual_time(self) -> int:
        return sum(map(lambda tes: tes.get_duration(), self.time_entry_slices))

    def delta(self) -> int:
        return self.actual_time() - self.target_time()

    def delta_percentage(self) -> float:
        if self.target_time() > 0:
            return self.delta() / self.target_time() * 100
        else:
            return None

    def __repr__(self):
        return (
            "<Day("
            f"date={self.date};"
            f"target_time={self.target_time()};"
            f"actual_time={self.actual_time()})>"
        )


class TimeEntrySlice:
    def __init__(self, time_entry: TimeEntry, start: datetime, end: datetime) -> None:
        self.time_entry = time_entry
        self.start = start
        self.end = end

    def get_duration(self):
        return int((self.end - self.start).total_seconds())


class DayAggregate:
    def __init__(self, start_date: date, end_date: date):
        self.days = set()
        self.start = start_date
        self.end = end_date
        self.max_days = (end_date - start_date).days + 1

    @classmethod
    def get_key_from_date(cls, day_date: date) -> tuple:
        raise NotImplementedError("Not implemented yet!")

    def days_with_target_time(self) -> tuple:
        return len(set(filter(lambda day: day.target_time() > 0, self.days)))

    def days_with_actual_time(self) -> tuple:
        return len(set(filter(lambda day: day.actual_time() > 0, self.days)))

    def get_key(self) -> tuple:
        return __class__.get_key_from_date(self.start)

    def target_time(self) -> int:
        return sum(map(lambda x: x.target_time(), self.days))

    def actual_time(self) -> int:
        return sum(map(lambda x: x.actual_time(), self.days))

    def delta(self) -> int:
        return self.actual_time() - self.target_time()


class Week(DayAggregate):
    def __init__(self, year: int, week: int):
        start = date.fromisocalendar(year, week, 1)
        end = date.fromisocalendar(year, week, 7)
        super().__init__(start, end)
        self.year = year
        self.week = week

    @classmethod
    def get_key_from_date(cls, day_date: date) -> tuple:
        isocal = day_date.isocalendar()
        return isocal.year, isocal.week

    def get_key(self) -> tuple:
        return __class__.get_key_from_date(self.start)

    def __repr__(self):
        return (
            "<Week("
            f"key={self.get_key()};"
            f"target_time={self.target_time()};"
            f"actual_time={self.actual_time()})>"
        )


class Month(DayAggregate):
    def __init__(self, year: int, month: int):
        start = date(year, month, 1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) + timedelta(
            days=-1
        )
        super().__init__(start, end)
        self.year = year
        self.month = month

    @classmethod
    def get_key_from_date(cls, day_date: date) -> tuple:
        return day_date.year, day_date.month

    def get_key(self) -> tuple:
        return __class__.get_key_from_date(self.start)

    def __repr__(self):
        return (
            "<Month("
            f"key={self.get_key()};"
            f"target_time={self.target_time()};"
            f"actual_time={self.actual_time()})>"
        )


class Quarter(DayAggregate):
    def __init__(self, year: int, quarter: int):
        start = date(year, (quarter - 1) * 3 + 1, 1)
        end = (
            (start + relativedelta(months=2)).replace(day=28) + timedelta(days=4)
        ).replace(day=1) + timedelta(days=-1)
        super().__init__(start, end)
        self.year = year
        self.quarter = quarter

    @classmethod
    def get_key_from_date(cls, day_date: date) -> tuple:
        return day_date.year, (day_date.month - 1) // 3 + 1

    def get_key(self) -> tuple:
        return __class__.get_key_from_date(self.start)

    def __repr__(self):
        return (
            "<Quarter("
            f"key={self.get_key()};"
            f"target_time={self.target_time()};"
            f"actual_time={self.actual_time()})>"
        )


class Year(DayAggregate):
    def __init__(self, year: int):
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        super().__init__(start, end)
        self.year = year

    @classmethod
    def get_key_from_date(cls, day_date: date) -> int:
        return day_date.year

    def get_key(self) -> tuple:
        return __class__.get_key_from_date(self.start)

    def __repr__(self):
        return (
            "<Year("
            f"key={self.get_key()};"
            f"target_time={self.target_time()};"
            f"actual_time={self.actual_time()})>"
        )


class All(DayAggregate):
    def __init__(self, start: date, end: date):
        start = start
        end = end
        super().__init__(start, end)

    def __repr__(self):
        return (
            "<All("
            f"target_time={self.target_time()};"
            f"actual_time={self.actual_time()})>"
        )


class Report:
    def __init__(
        self,
        user: User,
        workspace: Workspace,
        start_date: date,
        end_date: date,
        days: dict,
    ) -> None:
        self.user = user
        self.workspace = workspace
        self.start_date = start_date
        self.end_date = end_date
        self.days = days
        self.weeks = {}
        self.months = {}
        self.quarters = {}
        self.years = {}
        self.all = All(start_date, end_date)

    def running_delta(self):
        running_delta = 0
        for day in self.days.values():
            running_delta += day.delta()

        return running_delta


class Resolver:
    TIMEZONE_TOLERANCE_HOURS = 15

    @classmethod
    def create_report(
        cls, user: User, workspace: Workspace, start_date: date, end_date: date
    ):
        report = Report(
            user=user,
            workspace=workspace,
            start_date=start_date,
            end_date=end_date,
            days=Resolver.init_day_objects(start_date, end_date),
        )

        # process schedules
        schedules = Schedule.objects(user=user, workspace=workspace)
        for schedule in schedules:
            Resolver.apply_schedule(report.days, schedule, start_date, end_date)

        # process events
        events = Event.objects(user=user, workspace=workspace)
        for event in events:
            Resolver.apply_event(report.days, event, start_date, end_date)

        # process time entries
        timezone_tolerance = timedelta(hours=__class__.TIMEZONE_TOLERANCE_HOURS)
        start_date_with_offset = (
            datetime.combine(start_date, datetime.min.time()) - timezone_tolerance
        )
        end_date_with_offset = (
            datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            + timezone_tolerance
        )

        time_entries = TimeEntry.objects(
            Q(user=user)
            & Q(workspace=workspace)
            & (
                Q(started_at__gte=start_date_with_offset)
                & Q(started_at__lte=end_date_with_offset)
                | Q(stopped_at__gte=start_date_with_offset)
                & Q(stopped_at__lte=end_date_with_offset)
                | Q(started_at__lte=start_date_with_offset)
                & Q(stopped_at__gte=end_date_with_offset)
            )
        )
        for time_entry in time_entries:
            Resolver.apply_time_entry(report.days, time_entry)

        # aggregate days
        for day in report.days.values():
            week_key = Week.get_key_from_date(day.date)
            if week_key not in report.weeks:
                report.weeks[week_key] = Week(*week_key)
            report.weeks[week_key].days.add(day)

            month_key = Month.get_key_from_date(day.date)
            if month_key not in report.months:
                report.months[month_key] = Month(*month_key)
            report.months[month_key].days.add(day)

            quarter_key = Quarter.get_key_from_date(day.date)
            if quarter_key not in report.quarters:
                report.quarters[quarter_key] = Quarter(*quarter_key)
            report.quarters[quarter_key].days.add(day)

            year_key = Year.get_key_from_date(day.date)
            if year_key not in report.years:
                report.years[year_key] = Year(year_key)
            report.years[year_key].days.add(day)

            report.all.days.add(day)

        return report

    @classmethod
    def apply_schedule(
        cls, days: list[Day], schedule: Schedule, start_date: date, end_date: date
    ):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())

        if schedule.rrule is not None:
            rrule = rrulestr(schedule.rrule, dtstart=schedule.start_date)
            apply_dates = list(rrule.between(start_dt, end_dt, inc=True))
        else:
            apply_dates = [schedule.start_date]

        for apply_date in apply_dates:
            day_key = Day.get_id_by_day(apply_date)
            if day_key in days:
                days[day_key].schedules.add(schedule)

    @classmethod
    def apply_event(
        cls, days: list[Day], event: Event, start_date: date, end_date: date
    ):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())

        if event.rrule is not None:
            rrule = rrulestr(event.rrule, dtstart=event.start_date)
            apply_dates = list(rrule.between(start_dt, end_dt, inc=True))
        else:
            apply_dates = [event.start_date]

        for apply_date in apply_dates:
            day_key = Day.get_id_by_day(apply_date)
            if day_key in days:
                days[day_key].events.add(event)

    @classmethod
    def apply_time_entry(cls, days: list[Day], time_entry: TimeEntry):
        started_at_local = time_entry.started_at + timedelta(
            seconds=time_entry.started_at_offset
        )
        stopped_at_local = time_entry.stopped_at + timedelta(
            seconds=time_entry.stopped_at_offset
        )

        last_slice = False
        while True:
            if started_at_local.date() == stopped_at_local.date():
                time_entry_slice = TimeEntrySlice(
                    time_entry, started_at_local, stopped_at_local
                )
                last_slice = True
            else:
                next_midnight = started_at_local.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                time_entry_slice = TimeEntrySlice(
                    time_entry, started_at_local, next_midnight
                )
                started_at_local = next_midnight

            day_key = Day.get_id_by_day(time_entry_slice.start.date())
            if day_key in days:
                days[day_key].time_entry_slices.add(time_entry_slice)

            if last_slice:
                break

    @classmethod
    def init_day_objects(cls, start_date: date, end_date: date) -> dict[Day]:
        day_dates = Resolver.get_date_range(start_date, end_date)
        result = {}
        for day_date in day_dates:
            day = Day(day_date)
            result[day.get_id()] = day
        return result

    @classmethod
    def get_date_range(cls, start: date, end: date) -> list[date]:
        delta = end - start
        result = []
        for i in range(delta.days + 1):
            day_date = start + timedelta(days=i)
            result.append(day_date)

        return result


class CalendarSync:
    ANNOTATION_PREFIX = "ttc-"
    TYPE_SCHEDULE = "schedule"
    TYPE_EVENT = "event"
    ANNOTATION_PATTERN = re.compile(
        r"^(?:<span>|<br/?>)*"
        + ANNOTATION_PREFIX
        + r"("
        + TYPE_SCHEDULE
        + r"|"
        + TYPE_EVENT
        + r")((?::\w+=[\w\.-]+)+)(?:</span>|<br/?>)*$"
    )

    def fetch_calendar(self, url: str) -> Calendar:
        ics = httpx.get(url, timeout=20)

        return Calendar.from_ical(ics.content)

    def get_existing_documents_with_uid(
        self, document_cls: Document, user: User, workspace: Workspace
    ) -> dict:
        document_list = document_cls.objects(user=user, workspace=workspace)

        result = {}
        for document in document_list:
            result[document.source_uid] = document

        return result

    def filter_ical_components(self, ical: Calendar) -> list[tuple]:
        result = []
        for component in ical.walk():
            if component.name == "VEVENT" and "DESCRIPTION" in component:
                match = self.ANNOTATION_PATTERN.search(component["DESCRIPTION"])
                if match:
                    annotation_type = match.group(1)
                    annotation_option_strings = match.group(2).split(":")[1:]

                    annotation_options = {}
                    for part in annotation_option_strings:
                        key_value = part.split("=", 1)
                        annotation_options[key_value[0]] = key_value[1]

                    result.append((component, annotation_type, annotation_options))
        return result

    def create_or_update_schedule(
        self,
        schedules: dict,
        component: object,
        annotation_options: dict,
        user: User,
        workspace: Workspace,
    ) -> tuple[Schedule, bool]:
        created = component["UID"] not in schedules
        if created:
            schedule = Schedule(
                source_uid=component["UID"], user=user, workspace=workspace
            )
        else:
            schedule = schedules[component["UID"]]

        schedule.name = component["SUMMARY"]
        schedule.target = annotation_options.get("target", 0)
        schedule.start_date = component["DTSTART"].dt
        if "RRULE" in component:
            schedule.rrule = component["RRULE"].to_ical().decode()
        else:
            schedule.rrule = None

        return schedule, created

    def create_or_update_event(
        self,
        events: dict,
        component: object,
        annotation_options: dict,
        user: User,
        workspace: Workspace,
    ) -> tuple[Event, bool]:
        created = component["UID"] not in events
        if created:
            event = Event(source_uid=component["UID"], user=user, workspace=workspace)
        else:
            event = events[component["UID"]]

        event.name = component["SUMMARY"]
        event.mod_relative = float(annotation_options.get("rel", 0.0))
        event.mod_absolute = int(annotation_options.get("abs", 0))
        event.start_date = component["DTSTART"].dt
        if "RRULE" in component:
            event.rrule = component["RRULE"].to_ical().decode()
        else:
            event.rrule = None

        return event, created

    def update_user(
        self, user: User, next_calendar_sync: int, is_calendar_sync=False
    ) -> User:
        user.next_calendar_sync_at = datetime.now(timezone.utc) + timedelta(
            seconds=next_calendar_sync
        )

        if is_calendar_sync:
            user.last_calendar_sync_at = datetime.now(timezone.utc)

        return user.save()
