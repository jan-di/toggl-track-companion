from calendar import day_abbr
from datetime import datetime
from app.repository.app import (
    ScheduleExceptionRepository,
    ScheduleRepository,
)
from app.repository.toggl import TimeEntryRepository
from .models import Report


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


def analyze(session, toggl_user, user):
    now = datetime.now()

    schedule_repository = ScheduleRepository(session)
    schedule_exception_repository = ScheduleExceptionRepository(session)
    time_entry_repository = TimeEntryRepository(session)

    for toggl_organization in toggl_user.organizations:
        for toggl_workspace in toggl_organization.workspaces:

            schedules = schedule_repository.get_by_date_range(
                toggl_user, toggl_workspace, user.start, now.date()
            )
            schedule_exceptions = (
                schedule_exception_repository.get_by_user_and_workspace(
                    toggl_user=toggl_user, toggl_workspace=toggl_workspace
                )
            )
            time_entries = time_entry_repository.get_by_date_range(
                toggl_user, toggl_workspace, user.start, now
            )

            report = Report(
                toggl_user=toggl_user,
                toggl_workspace=toggl_workspace,
                start_date=user.start,
                end_date=now.date(),
                schedules=schedules,
                schedule_exceptions=schedule_exceptions,
                time_entries=time_entries,
            )
            text_report = legacy_text_report(report, schedules)

    return text_report, report


def legacy_text_report(report, schedules):
    result = ""
    result += f"User: {report.toggl_user.fullname} > Org: {report.toggl_workspace.organization.name} > Workspace: {report.toggl_workspace.name}\n"
    result += "\n"

    for schedule in schedules:
        result += (
            f"Start: {schedule.start}; "
            f"End: {schedule.end}; "
            f"{day_abbr[0]}: {schedule.day0}; "
            f"{day_abbr[1]}: {schedule.day1}; "
            f"{day_abbr[2]}: {schedule.day2}; "
            f"{day_abbr[3]}: {schedule.day3}; "
            f"{day_abbr[4]}: {schedule.day4}; "
            f"{day_abbr[5]}: {schedule.day5}; "
            f"{day_abbr[6]}: {schedule.day6}; "
            "\n"
        )

    result += "\n"
    for day in report.days.values():
        result += f"{day.date} {day_abbr[day.date.weekday()] } -> Target: {str(day.target_time).rjust(5)}; Actual: {str(day.actual_time).rjust(5)}; Delta: {str(day.delta()).rjust(6)}; Exceptions: {','.join(map(lambda x:f'{x.description} (*{x.factor}, +{x.addend})', day.exceptions))}\n"

    result += "\n"
    running_delta = 0
    for week in report.weeks.values():
        running_delta += week.delta()
        result += f"{week.year}-{week.week} ({len(week.days)} Days) -> Target: {format_time(week.target_time())}; Actual: {format_time(week.actual_time())}; Delta: {format_time(week.delta())}; FullfillmentRate: {format_percentage(week.fullfillment_rate())}; RunningDelta: {format_time(running_delta)}\n"

    return result
