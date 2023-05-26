from threading import Event
import logging
import signal
from datetime import datetime

from src.db.schema import User
from src.toggl import TogglApi, TogglUpdater


class Updater:
    def __init__(self, sync_interval: int) -> None:
        self.exit_event = Event()
        self.sync_interval = sync_interval
        self.toggl_updater = TogglUpdater()
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
        users = User.objects(next_sync_at__lte=datetime.now())
        logging.info(f"Found %s users to sync", len(users))

        for user in users:
            toggl_api = TogglApi(api_token=user.api_token)

            _, toggl_user, _ = toggl_api.get_me()
            self.toggl_updater.create_or_update_user(toggl_user, self.sync_interval)
            
            _, organizations, _ = toggl_api.get_my_organizations()
            for organization in organizations:
                self.toggl_updater.create_or_update_organization(organization)

            _, workspaces, _ = toggl_api.get_my_workspaces()
            for workspace in workspaces:
                self.toggl_updater.create_or_update_workspace(workspace)
