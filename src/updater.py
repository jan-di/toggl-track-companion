from threading import Event
import logging
import signal

from src.db.schema import User
from src.toggl import TogglApi, TogglUpdater


class Updater:
    def __init__(self) -> None:
        self.exit_event = Event()
        exit_signals = {1: "SIGHUP", 2: "SIGINT", 15: "SIGTERM"}

        def exit_loop(signal_number, _frame):
            logging.info(
                "Interrupted by %s, shutting down", exit_signals[signal_number]
            )
            self.exit_event.set()

        for signal_string in exit_signals.values():
            signal.signal(getattr(signal, signal_string), exit_loop)

    def run(self):
        # calendar_sync = CalendarSync()
        while not self.exit_event.is_set():
            self.cycle()
            self.exit_event.wait(5)

    def cycle(self):
        users = User.objects()
        toggl_updater = TogglUpdater()

        for user in users:
            toggl_api = TogglApi(api_token=user.api_token)

            _, toggl_user, _ = toggl_api.get_me()
            toggl_updater.create_or_update_user(toggl_user)
            
            _, organizations, _ = toggl_api.get_my_organizations()
            for organization in organizations:
                toggl_updater.create_or_update_organization(organization)

            _, workspaces, _ = toggl_api.get_my_workspaces()
            for workspace in workspaces:
                toggl_updater.create_or_update_workspace(workspace)
