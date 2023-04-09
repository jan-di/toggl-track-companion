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
