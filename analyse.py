# from re import X
# import httpx
from calendar import day_abbr
from datetime import datetime, timedelta, date
from dateutil.rrule import rrulestr
from models.app import ScheduleException, User, Schedule
from models.toggl import TimeEntry, User as TogglUser
from repository.app import ScheduleExceptionRepository, ScheduleRepository
from repository.toggl import TimeEntryRepository
from util import load_config, Database


class Day:
    date = None
    target_time = None
    actual_time = None
    exceptions = None

    def __init__(self, date):
        self.date = date
        self.target_time = 0
        self.actual_time = 0
        self.exceptions = set()

    def delta(self):
        return self.actual_time - self.target_time

    def __repr__(self):
        return f"<Day(target_time={self.target_time};actual_time={self.actual_time})>"


class Week:
    days = None

    def __init__(self, year: int, week: int):
        self.days = set()
        self.year = year
        self.week = week

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


def get_datetime_range(start: date, end: date):
    delta = end - start
    result = []

    for i in range(delta.days + 1):
        dt_day = start + timedelta(days=i)
        result.append(dt_day)

    return result


def apply_schedule(
    days: list[Day], schedule: Schedule, start_limit: date, end_limit: date
):
    schedule_days = get_datetime_range(
        max(start_limit, schedule.start),
        min(end_limit, schedule.end if schedule.end is not None else end_limit),
    )
    for schedule_day in schedule_days:
        if schedule_day.strftime("%Y-%m-%d") in days:
            days[schedule_day.strftime("%Y-%m-%d")].target_time = getattr(
                schedule, f"day{schedule_day.weekday()}"
            )


def apply_schedule_exception(
    days: list[Day], exception: ScheduleException, start_limit: date, end_limit: date
):
    rrule = rrulestr(exception.rrule, dtstart=exception.start)

    start = datetime.combine(start_limit, datetime.min.time())
    end = datetime.combine(end_limit, datetime.min.time())

    ex_days = list(rrule.between(start, end, inc=True))

    for ex_day in ex_days:
        day_key = ex_day.strftime("%Y-%m-%d")
        if day_key in days:
            days[day_key].target_time = int(
                days[day_key].target_time * exception.factor
            )
            days[day_key].target_time += exception.addend
            days[day_key].exceptions.add(exception)


def apply_time_entries(days: list[Day], time_entries: list[TimeEntry]):
    for time_entry in time_entries:
        day_key = time_entry.start.strftime("%Y-%m-%d")
        if day_key in days:
            days[day_key].actual_time += (time_entry.stop - time_entry.start).seconds


def format_time(seconds: int):
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02}:{mm:02}:{ss:02}"


def format_percentage(percent: float, precision: int = 2):
    return (
        f"{round(percent*100, precision): >{4 + precision}}%"
        if percent is not None
        else "-" * (5 + precision)
    )


def main():
    config = load_config()
    database = Database(config["DATABASE_URI"])

    now = datetime.now()

    with database.get_session() as session:
        schedule_repository = ScheduleRepository(session)
        schedule_exception_repository = ScheduleExceptionRepository(session)

        for user in session.query(User).all():
            toggl_user = user.toggl_user

            for toggl_organization in toggl_user.organizations:
                for toggl_workspace in toggl_organization.workspaces:
                    print(
                        f"User: {toggl_user.fullname} > Org: {toggl_organization.name} > Workspace: {toggl_workspace.name}"
                    )
                    print("")

                    days = {}
                    delta = now.date() - user.start
                    for i in range(delta.days + 1):
                        dt_day = user.start + timedelta(days=i)
                        day = Day(dt_day)
                        days[dt_day.strftime("%Y-%m-%d")] = day

                    # Get all relevant work schedules

                    schedules = schedule_repository.get_by_date_range(
                        toggl_user, toggl_workspace, user.start, now.date()
                    )

                    for schedule in schedules:
                        apply_schedule(days, schedule, user.start, now.date())

                    for schedule in schedules:
                        print(
                            f"Start: {schedule.start}; "
                            f"End: {schedule.end}; "
                            f"{day_abbr[0]}: {schedule.day0}; "
                            f"{day_abbr[1]}: {schedule.day1}; "
                            f"{day_abbr[2]}: {schedule.day2}; "
                            f"{day_abbr[3]}: {schedule.day3}; "
                            f"{day_abbr[4]}: {schedule.day4}; "
                            f"{day_abbr[5]}: {schedule.day5}; "
                            f"{day_abbr[6]}: {schedule.day6}; "
                        )
                    print("")

                    # Schedule Exceptions
                    schedule_exceptions = (
                        schedule_exception_repository.get_by_user_and_workspace(
                            toggl_user=toggl_user, toggl_workspace=toggl_workspace
                        )
                    )
                    for schedule_exception in schedule_exceptions:
                        apply_schedule_exception(
                            days, schedule_exception, user.start, now.date()
                        )

                    # Time Entries
                    time_entry_repository = TimeEntryRepository(session)
                    time_entries = time_entry_repository.get_by_date_range(
                        toggl_user, toggl_workspace, user.start, now
                    )

                    apply_time_entries(days, time_entries)

                    for day, val in days.items():
                        print(
                            f"{day} {day_abbr[val.date.weekday()] } -> Target: {str(val.target_time).rjust(5)}; Actual: {str(val.actual_time).rjust(5)}; Delta: {str(val.delta()).rjust(6)}; Exceptions: {','.join(map(lambda x:f'{x.description} (*{x.factor}, +{x.addend})', val.exceptions))}"
                        )

                    print("")

                    weeks = {}
                    for day, val in days.items():
                        kw = val.date.isocalendar()

                        if (kw.year, kw.week) not in weeks:
                            weeks[kw.year, kw.week] = Week(
                                kw.year,
                                kw.week,
                            )

                        weeks[kw.year, kw.week].days.add(val)

                    running_delta = 0
                    for week, val in weeks.items():
                        running_delta += val.delta()
                        print(
                            f"{val.year}-{val.week} ({len(val.days)} Days) -> Target: {format_time(val.target_time())}; Actual: {format_time(val.actual_time())}; Delta: {format_time(val.delta())}; FullfillmentRate: {format_percentage(val.fullfillment_rate())}; RunningDelta: {format_time(running_delta)}"
                        )


if __name__ == "__main__":
    main()
