from threading import Event
import logging
import signal
from datetime import datetime, date
import json

from src.db.schema import User, Workspace
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
            self.exit_event.wait(50)

    def cycle(self):
        # users = User.objects(next_sync_at__lte=datetime.now())
        users = User.objects()
        logging.info("Found %s users to sync", len(users))

        for user in users:
            toggl_api = TogglApi(api_token=user.api_token)

            _, toggl_user = toggl_api.get_me()
            self.toggl_updater.create_or_update_user(toggl_user, self.sync_interval)
            
            _, organizations = toggl_api.get_my_organizations()
            for organization in organizations:
                self.toggl_updater.create_or_update_organization(organization)

            _, workspace_datasets = toggl_api.get_my_workspaces()
            for workspace_data in workspace_datasets:
                workspace = self.toggl_updater.create_or_update_workspace(workspace_data)

                time_entry_report = []

                for year in range(TogglUpdater.MIN_YEAR, date.today().year + 1):
                    start_date = date(year, 1, 1)
                    end_date = date(year, 12, 31)

                    time_entry_datasets = toggl_api.search_time_entries(workspace.workspace_id, start_date, end_date)
                    time_entry_report += time_entry_datasets
