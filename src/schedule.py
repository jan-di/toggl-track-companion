import re
import httpx
from icalendar import Calendar
from src.db.schema import User, UserCalendar, Schedule, Event


class CalendarSync:
    pattern = re.compile(
        r"^(?:<span>)*ttr-(schedule|event)((?::\w+=\w+)+)(?:</span>)*$"
    )

    def get_users_to_sync(self) -> User:
        return User.objects()

    def sync_calendar(self, user_calendar: UserCalendar) -> None:
        ical = self._fetch_calendar(user_calendar.url)

        schedules = self._get_existing_documents_with_uid(Schedule, user_calendar)
        synced_schedule_uids = set()
        events = self._get_existing_documents_with_uid(Event, user_calendar)
        synced_event_uids = set()

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
                    elif annotation_type == "event":
                        event = self._create_or_update_event(
                            events, component, annotation_options, user_calendar
                        )
                        synced_event_uids.add(event.source_uid)
                        event.save()

        # delete schedules
        schedules_to_delete = set(schedules.keys()).difference(synced_schedule_uids)
        for schedule_uid in schedules_to_delete:
            schedules[schedule_uid].delete()

        # delete event
        events_to_delete = set(events.keys()).difference(synced_event_uids)
        for event_uid in events_to_delete:
            events[event_uid].delete()

    def _get_existing_documents_with_uid(
        self, document_cls, user_calendar: UserCalendar
    ) -> list:
        document_list = document_cls.objects(
            user_id=user_calendar.user_id,
            organization_id=user_calendar.organization_id,
            workspace_id=user_calendar.workspace_id,
        )

        result = {}
        for document in document_list:
            result[document["source_uid"]] = document

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
        else:
            schedule.rrule = None

        return schedule

    def _create_or_update_event(
        self, events, component, annotation_options, user_calendar: UserCalendar
    ):
        if component["UID"] not in events:
            event = Event()
            event.source_uid = component["UID"]
            event.user_id = user_calendar.user_id
            event.organization_id = user_calendar.organization_id
            event.workspace_id = user_calendar.workspace_id
        else:
            event = events[component["UID"]]

        event.name = component["SUMMARY"]
        event.factor = float(annotation_options.get("factor", 1.0))
        event.addend = int(annotation_options.get("addend", 0))
        event.start_date = component["DTSTART"].dt
        if "RRULE" in component:
            event.rrule = component["RRULE"].to_ical().decode()
        else:
            event.rrule = None

        return event

    def _fetch_calendar(self, url: str) -> Calendar:
        ics = httpx.get(url, timeout=20)

        calendar = Calendar.from_ical(ics.content)
        return calendar
