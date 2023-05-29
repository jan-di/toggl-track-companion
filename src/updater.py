from threading import Event
import logging
import signal
from datetime import date, datetime

from src.db.schema import User, Client, Tag, Project, TimeEntry
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
        users = User.objects()
        # users = User.objects(next_sync_at__lte=datetime.now())
        logging.info("Found %s users to sync", len(users))

        users_updated = 0
        organizations_created_updated = 0
        organizations_deleted = 0
        workspaces_created_updated = 0
        workspaces_deleted = 0
        time_entries_created_updated = 0
        time_entries_deleted = 0
        clients_created_updated = 0
        clients_deleted = 0
        projects_created_updated = 0
        projects_deleted = 0
        tags_created_updated = 0
        tags_deleted = 0

        for user in users:
            toggl_api = TogglApi(api_token=user.api_token)

            # update user
            user_data = toggl_api.get_me()
            user = self.toggl_updater.create_or_update_user_from_api(user_data, self.sync_interval)
            users_updated += 1

            # create/update organizations
            organization_dataset = toggl_api.get_my_organizations()
            for organization_data in organization_dataset:
                self.toggl_updater.create_or_update_organization_from_api(organization_data)
            organizations_created_updated += len(organization_dataset)

            # create/update workspaces
            workspace_dataset = toggl_api.get_my_workspaces()
            self.toggl_updater.update_user_workspaces_from_api(user, workspace_dataset)
            for workspace_data in workspace_dataset:
                workspace = self.toggl_updater.create_or_update_workspace_from_api(workspace_data)
                workspaces_created_updated += 1

                # create/update clients
                client_dataset = toggl_api.get_workspace_clients(workspace.workspace_id)
                for client_data in client_dataset:
                    self.toggl_updater.create_or_update_client_from_api(client_data)
                clients_created_updated = len(client_dataset)

                # create/update projects
                project_dataset = toggl_api.get_workspace_projects(workspace.workspace_id)
                for project_data in project_dataset:
                    self.toggl_updater.create_or_update_project_from_api(project_data)
                projects_created_updated = len(project_dataset)

                # create/update tags
                tag_dataset = toggl_api.get_workspace_tags(workspace.workspace_id)
                for tag_data in tag_dataset:
                    self.toggl_updater.create_or_update_tag_from_api(tag_data)
                tags_created_updated += len(tag_dataset)

                # create/update time entries
                time_entry_dataset = []
                for year in range(TogglUpdater.MIN_YEAR, date.today().year + 1):
                    start_date = date(year, 1, 1)
                    end_date = date(year, 12, 31)

                    time_entry_dataset += toggl_api.get_workspace_time_entries(workspace.workspace_id, start_date, end_date)
                for time_entry_data in time_entry_dataset:
                    self.toggl_updater.create_or_update_time_entry_from_report_api(time_entry_data, workspace.workspace_id)
                time_entries_created_updated += len(time_entry_dataset)

                # delete time entries
                remote_time_entry_ids = set(map(lambda d: d["time_entries"][0]["id"], time_entry_dataset))
                local_time_entry_ids = set(TimeEntry.objects(workspace_id=workspace.workspace_id).scalar("time_entry_id"))
                time_entry_ids_to_delete = local_time_entry_ids - remote_time_entry_ids
                self.toggl_updater.delete_time_entries_via_ids(time_entry_ids_to_delete)
                time_entries_deleted += len(time_entry_ids_to_delete)

                # delete tags
                remote_tag_ids = set(map(lambda d: d["id"], tag_dataset))
                local_tag_ids = set(Tag.objects(workspace_id=workspace.workspace_id).scalar("tag_id"))
                tag_ids_to_delete = local_tag_ids - remote_tag_ids
                self.toggl_updater.delete_tags_via_ids(tag_ids_to_delete)
                tags_deleted += len(tag_ids_to_delete)

                # delete projects
                remote_project_ids = set(map(lambda d: d["id"], project_dataset))
                local_project_ids = set(Project.objects(workspace_id=workspace.workspace_id).scalar("project_id"))
                project_ids_to_delete = local_project_ids - remote_project_ids
                self.toggl_updater.delete_projects_via_ids(project_ids_to_delete)
                projects_deleted += len(project_ids_to_delete)

                # delete clients
                remote_client_ids = set(map(lambda d: d["id"], client_dataset))
                local_client_ids = set(Client.objects(workspace_id=workspace.workspace_id).scalar("client_id"))
                client_ids_to_delete = local_client_ids - remote_client_ids
                self.toggl_updater.delete_clients_via_ids(client_ids_to_delete)
                clients_deleted += len(client_ids_to_delete)

        logging.info("Users updated: %i", users_updated)
        logging.info("Organizations created/updated: %i; deleted: %i (not implemented)", organizations_created_updated, organizations_deleted)
        logging.info("Clients created/updated: %i; deleted: %i (not implemented)", workspaces_created_updated, workspaces_deleted)
        logging.info("Clients created/updated: %i; deleted: %i", clients_created_updated, clients_deleted)
        logging.info("Projects created/updated: %i; deleted: %i", projects_created_updated, projects_deleted)
        logging.info("Tags created/updated: %i; deleted: %i", tags_created_updated, tags_deleted)
        logging.info("Time entries created/updated: %i; deleted %i", time_entries_created_updated, time_entries_deleted)
