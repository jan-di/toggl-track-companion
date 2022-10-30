from datetime import date, datetime, timedelta
from dateutil.rrule import rrulestr
from dateutil.relativedelta import relativedelta
from app.models.app import Schedule, ScheduleException
from app.models.toggl import TimeEntry, User, Workspace


class Report:
    def __init__(
        self,
        toggl_user: User,
        toggl_workspace: Workspace,
        start_date: date,
        end_date: date,
        schedules: list[Schedule],
        schedule_exceptions: list[ScheduleException],
        time_entries: list[TimeEntry],
    ):
        self.toggl_user = toggl_user
        self.toggl_workspace = toggl_workspace
        self.start_date = start_date
        self.end_date = end_date
        self.days = {}
        self.weeks = {}
        self.months = {}
        self.quarters = {}

        self.__init_days()
        for schedule in schedules:
            self.__apply_schedule(schedule)
        for schedule_exception in schedule_exceptions:
            self.__apply_schedule_exception(schedule_exception)
        for time_entry in time_entries:
            self.__apply_time_entry(time_entry)
        self.__aggregate_days()

    def __init_days(self) -> None:
        day_dates = Report.__get_datetime_range(self.start_date, self.end_date)
        for day_date in day_dates:
            day = Day(day_date)
            self.days[day.get_id()] = day

    def __apply_schedule(self, schedule: Schedule):
        actual_end_date = schedule.end if schedule.end is not None else self.end_date
        schedule_dates = Report.__get_datetime_range(
            max(self.start_date, schedule.start),
            min(self.end_date, actual_end_date),
        )

        for day_date in schedule_dates:
            day_key = Day.get_id_by_day(day_date)
            if day_key in self.days:
                self.days[day_key].target_time = getattr(
                    schedule, f"day{day_date.weekday()}"
                )

    def __apply_schedule_exception(self, exception: ScheduleException):
        rrule = rrulestr(exception.rrule, dtstart=exception.start)

        start = datetime.combine(self.start_date, datetime.min.time())
        end = datetime.combine(self.end_date, datetime.min.time())

        ex_dates = list(rrule.between(start, end, inc=True))

        for ex_date in ex_dates:
            day_key = Day.get_id_by_day(ex_date)
            if day_key in self.days:
                self.days[day_key].target_time = int(
                    self.days[day_key].target_time * exception.factor
                )
                self.days[day_key].target_time += exception.addend
                self.days[day_key].exceptions.add(exception)

    def __apply_time_entry(self, time_entry: TimeEntry):
        day_key = Day.get_id_by_day(time_entry.start)
        if day_key in self.days:
            self.days[day_key].time_entries += 1
            self.days[day_key].actual_time += (
                time_entry.stop - time_entry.start
            ).seconds

    def __aggregate_days(self):
        for day in self.days.values():
            week_key = Week.get_key_from_date(day.date)
            if week_key not in self.weeks:
                self.weeks[week_key] = Week(*week_key)
            self.weeks[week_key].days.add(day)

            month_key = Month.get_key_from_date(day.date)
            if month_key not in self.months:
                self.months[month_key] = Month(*month_key)
            self.months[month_key].days.add(day)

            quarter_key = Quarter.get_key_from_date(day.date)
            if quarter_key not in self.quarters:
                self.quarters[quarter_key] = Quarter(*quarter_key)
            self.quarters[quarter_key].days.add(day)

    @classmethod
    def __get_datetime_range(cls, start: date, end: date):
        delta = end - start
        result = []
        for i in range(delta.days + 1):
            dt_day = start + timedelta(days=i)
            result.append(dt_day)

        return result


class Day:
    def __init__(self, day_date: date):
        self.date = day_date
        self.target_time = 0
        self.actual_time = 0
        self.time_entries = 0
        self.exceptions = set()

    @classmethod
    def get_id_by_day(cls, day: date) -> str:
        return day.strftime("%Y-%m-%d")

    def get_id(self) -> str:
        return Day.get_id_by_day(self.date)

    def fullfillment_rate(self) -> float:
        return self.actual_time / self.target_time if self.target_time != 0 else None

    def delta(self):
        return self.actual_time - self.target_time

    def __repr__(self):
        return f"<Day(target_time={self.target_time};actual_time={self.actual_time})>"


class DayAggregate:
    def __init__(self, start: date, end: date):
        self.days = set()
        self.start = start
        self.end = end
        self.max_days = (end - start).days + 1

    @classmethod
    def get_key_from_date(cls, day_date: date) -> tuple:
        raise NotImplementedError("Not implemented!")

    def days_with_target_time(self) -> tuple:
        return len(set(filter(lambda day: day.target_time > 0, self.days)))

    def days_with_actual_time(self) -> tuple:
        return len(set(filter(lambda day: day.actual_time > 0, self.days)))

    def get_key(self) -> tuple:
        return DayAggregate.get_key_from_date(self.start)

    def target_time(self) -> int:
        return sum(map(lambda x: x.target_time, self.days))

    def actual_time(self) -> int:
        return sum(map(lambda x: x.actual_time, self.days))

    def fullfillment_rate(self) -> float:
        return (
            self.actual_time() / self.target_time() if self.target_time() != 0 else None
        )

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
