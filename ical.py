# import re
  
from threading import Event
import logging
import signal

from src.util.config import Config
from src.util.log import Log
from src.db.database import Database
from src.schedule import CalendarSync


def main():
    Log()
    config = Config()
    database = Database(config.database_uri)

    exit_event = Event()
    exit_signals = {1: "SIGHUP", 2: "SIGINT", 15: "SIGTERM"}

    def exit_loop(signal_number, _frame):
        logging.info("Interrupted by %s, shutting down", exit_signals[signal_number])
        exit_event.set()

    for signal_string in exit_signals.values():
        signal.signal(getattr(signal, signal_string), exit_loop)

    calendar_sync = CalendarSync()
    while not exit_event.is_set():
        cycle(calendar_sync)
        exit_event.wait(5)

    database.disconnect()
    logging.info("Exit")


def cycle(calendar_sync):
    logging.info("Start sync cycle")

    users = calendar_sync.get_users_to_sync()
    logging.info("Found %i users to sync", len(users))

    for user in users:
        for calendar in user.calendars:
            calendar_sync.sync_calendar(calendar)


if __name__ == "__main__":
    main()

# ================================================

# pattern = re.compile(r"^(?:<span>)*ttr-(schedule|event)((?::\w+=\w+)+)(?:</span>)*$")

# def sync_calendar(user_id=1, organization_id=1, workspace_id=1):
#     schedule_list = Schedule.objects(
#         user_id=user_id, organization_id=organization_id, workspace_id=workspace_id
#     )

#     schedules = {}
#     for schedule in schedule_list:
#         schedules[schedule["source_uid"]] = schedule
#     synced_uids = set()

#     for component in gcal.walk():
#         if component.name == "VEVENT":
#             print(f"EVENT: {component['SUMMARY']}")
#             match = pattern.search(component["DESCRIPTION"])
#             if match:
#                 annotation_type = match.group(1)
#                 annotation_option_string = match.group(2).split(":")[1:]

#                 annotation_options = {}
#                 for part in annotation_option_string:
#                     kv = part.split("=", 1)
#                     annotation_options[kv[0]] = kv[1]

#                 if annotation_type == "schedule":
#                     if component["UID"] not in schedules:
#                         schedule = Schedule()
#                         schedule.source_uid = component["UID"]
#                         schedule.user_id = user_id
#                         schedule.organization_id = organization_id
#                         schedule.workspace_id = workspace_id
#                     else:
#                         schedule = schedules[component["UID"]]
#                     synced_uids.add(component["UID"])

#                     schedule.name = component["SUMMARY"]
#                     schedule.target = annotation_options.get("target", 0)
#                     schedule.start_date = component["DTSTART"].dt
#                     if "RRULE" in component:
#                         schedule.rrule = component["RRULE"].to_ical().decode()

#                     schedule.save()

#                 print(component["DTSTART"].to_ical())
#                 print(annotation_type)
#                 print(annotation_options)

#     deleted_schedules = set(schedules.keys()).difference(synced_uids)
#     print(deleted_schedules)

#     for delete_schedule_key in deleted_schedules:
#         schedules[delete_schedule_key].delete()


# sync_calendar()

# client = MongoClient("mongodb://mongodb:27017")
# db = client.test
# col = db.test
# tutorial1 = {
#     "title": "Working With JSON Data in Python",
#     "author": "Lucas",
#     "contributors": ["Aldren", "Dan", "Joanna"],
#     "url": "https://realpython.com/python-json/",
# }

# col.insert_one(tutorial1)
