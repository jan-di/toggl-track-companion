import re
import httpx
from icalendar import Calendar
from mongoengine import Document
from src.db.schema import User, Workspace, Schedule, Event


class CalendarSync:
    ANNOTATION_PREFIX = "ttc-"
    TYPE_SCHEDULE = "schedule"
    TYPE_EVENT = "event"
    ANNOTATION_PATTERN = re.compile(
        r"^(?:<span>)*"
        + ANNOTATION_PREFIX
        + r"("
        + TYPE_SCHEDULE
        + r"|"
        + TYPE_EVENT
        + r")((?::\w+=\w+)+)(?:</span>)*$"
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
            if component.name == "VEVENT":
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
        event.factor = float(annotation_options.get("factor", 1.0))
        event.addend = int(annotation_options.get("addend", 0))
        event.start_date = component["DTSTART"].dt
        if "RRULE" in component:
            event.rrule = component["RRULE"].to_ical().decode()
        else:
            event.rrule = None

        return event, created
