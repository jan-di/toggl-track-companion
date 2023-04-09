import re
import httpx
from icalendar import Calendar
from src.db.schema import User, UserCalendar, Schedule


class CalendarSync:
    pattern = re.compile(
        r"^(?:<span>)*ttr-(schedule|event)((?::\w+=\w+)+)(?:</span>)*$"
    )

    def get_users_to_sync(self) -> User:
        return User.objects()

    def sync_calendar(self, user_calendar: UserCalendar) -> None:
        ical = self._fetch_calendar(user_calendar.url)

        schedules = self._get_existing_schedules_with_uid(user_calendar)
        synced_schedule_uids = set()

        for component in ical.walk():
            if component.name == "VEVENT":
                match = self.pattern.search(component["DESCRIPTION"])
                if match:
                    annotation_type = match.group(1)
                    annotation_option_strings = match.group(2).split(":")[1:]

                    annotation_options = {}
                    for part in annotation_option_strings:
                        key_value = part.split("=", 1)
                        annotation_options[key_value[0]] = key_value[1]

                    if annotation_type == "schedule":
                        schedule = self._create_or_update_schedule(
                            schedules, component, annotation_options, user_calendar
                        )
                        synced_schedule_uids.add(schedule.source_uid)
                        schedule.save()

        # delete schedules
        schedules_to_delete = set(schedules.keys()).difference(synced_schedule_uids)
        for schedule_uid in schedules_to_delete:
            schedules[schedule_uid].delete()

    def _get_existing_schedules_with_uid(
        self, user_calendar: UserCalendar
    ) -> list[Schedule]:
        schedule_list = Schedule.objects(
            user_id=user_calendar.user_id,
            organization_id=user_calendar.organization_id,
            workspace_id=user_calendar.workspace_id,
        )

        result = {}
        for schedule in schedule_list:
            result[schedule["source_uid"]] = schedule

        return result

    def _create_or_update_schedule(
        self, schedules, component, annotation_options, user_calendar: UserCalendar
    ):
        if component["UID"] not in schedules:
            schedule = Schedule()
            schedule.source_uid = component["UID"]
            schedule.user_id = user_calendar.user_id
            schedule.organization_id = user_calendar.organization_id
            schedule.workspace_id = user_calendar.workspace_id
        else:
            schedule = schedules[component["UID"]]

        schedule.name = component["SUMMARY"]
        schedule.target = annotation_options.get("target", 0)
        schedule.start_date = component["DTSTART"].dt
        if "RRULE" in component:
            schedule.rrule = component["RRULE"].to_ical().decode()

        return schedule

    def _fetch_calendar(self, url: str) -> Calendar:
        ics = httpx.get(url, timeout=20)

        calendar = Calendar.from_ical(ics.content)
        return calendar
