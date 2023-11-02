from threading import Event as ThreadingEvent
import logging
import signal
from datetime import date, datetime, timezone
from flask import Flask

from src.toggl.api import TogglApi
from src.toggl.model import SubscriptionData, EventFilterData
from src.db.entity import (
    User,
    Client,
    Tag,
    Project,
    TimeEntry,
    Workspace,
    Organization,
    Schedule,
    Event,
)
from src.schedule import CalendarSync


class Updater:
    def __init__(
        self,
        sync_interval_calendar: int,
        sync_interval_toggl: int,
        flask: Flask,
        server_id: str,
    ) -> None:
        self.exit_event = ThreadingEvent()
        self.sync_interval_calendar = sync_interval_calendar
        self.sync_interval_toggl = sync_interval_toggl
        self.flask = flask
        self.server_id = server_id
        exit_signals = {1: "SIGHUP", 2: "SIGINT", 15: "SIGTERM"}

        def exit_loop(signal_number, _frame):
            logging.info(
                "Interrupted by %s, shutting down", exit_signals[signal_number]
            )
            self.exit_event.set()

        for signal_string in exit_signals.values():
            signal.signal(getattr(signal, signal_string), exit_loop)

    def run(self):
        while not self.exit_event.is_set():
            self.cycle()
            self.exit_event.wait(10)

    def cycle(self):
        self.sync_toggl()
        self.sync_calendars()

    def sync_toggl(self):
        users = User.objects(next_toggl_sync_at__lte=datetime.now(timezone.utc))
        logging.info("Found %s users to sync with toggl track", len(users))

        if len(users) > 0:
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
                me_data = toggl_api.get_me()
                user = User.create_or_update_via_api_data(
                    me_data, self.sync_interval_toggl, is_toggl_sync=True
                )
                users_updated += 1

                # create/update organizations
                organization_dataset = toggl_api.get_my_organizations()
                for organization_data in organization_dataset:
                    Organization.create_or_update_via_api_data(organization_data)
                organizations_created_updated += len(organization_dataset)

                # create/update workspaces
                workspace_dataset = toggl_api.get_my_workspaces()
                workspaces = []
                for workspace_data in workspace_dataset:
                    workspaces.append(
                        Workspace.create_or_update_via_api_data(workspace_data)
                    )
                user = User.update_workspaces_via_api_data(user, workspace_dataset)
                workspaces_created_updated += len(workspaces)

                for user_workspace in user.workspaces:
                    # get existing webhooks
                    subscriptions = toggl_api.get_workspace_subscriptions(
                        user_workspace.workspace.workspace_id
                    )

                    # prepare data for new webhook
                    webhook_description = f"ttc/{self.server_id}/{user.user_id}"
                    webhook_url = self.flask.url_for(
                        "webhook",
                        workspace_id=user_workspace.workspace.workspace_id,
                        user_id=user.user_id,
                    )
                    new_webhook = SubscriptionData(
                        description=webhook_description,
                        enabled=True,
                        event_filters=[
                            EventFilterData(entity="client", action="*"),
                            EventFilterData(entity="project", action="*"),
                            EventFilterData(entity="tag", action="*"),
                            EventFilterData(entity="time_entry", action="*"),
                        ],
                        secret=user_workspace.subscription_token,
                        url_callback=webhook_url,
                    )

                    # check if webhook already exists
                    existing_webhook = None
                    for subscription in subscriptions:
                        if subscription.description == webhook_description:
                            existing_webhook = subscription
                            break

                    # create webhook if needed
                    if existing_webhook is None:
                        toggl_api.create_workspace_subscription(
                            user_workspace.workspace.workspace_id, new_webhook
                        )

                for workspace in workspaces:
                    # create/update clients
                    client_dataset = toggl_api.get_workspace_clients(
                        workspace.workspace_id
                    )
                    for client_data in client_dataset:
                        Client.create_or_update_via_api_data(client_data)
                    clients_created_updated = len(client_dataset)

                    # create/update projects
                    project_dataset = toggl_api.get_workspace_projects(
                        workspace.workspace_id
                    )
                    for project_data in project_dataset:
                        Project.create_or_update_via_api_data(project_data)

                    projects_created_updated = len(project_dataset)

                    # create/update tags
                    tag_dataset = toggl_api.get_workspace_tags(workspace.workspace_id)
                    for tag_data in tag_dataset:
                        Tag.create_or_update_via_api_data(tag_data)
                    tags_created_updated += len(tag_dataset)

                    # create/update time entries
                    time_entry_dataset = []
                    for year in range(TogglApi.MIN_YEAR, date.today().year + 1):
                        start_date = date(year, 1, 1)
                        end_date = date(year, 12, 31)

                        time_entry_dataset += (
                            toggl_api.get_workspace_time_entry_report_start_end(
                                workspace.workspace_id, start_date, end_date
                            )
                        )
                    for time_entry_data in time_entry_dataset:
                        TimeEntry.create_or_update_via_report_api_data(
                            time_entry_data, workspace.workspace_id
                        )
                    time_entries_created_updated += len(time_entry_dataset)

                    # delete time entries
                    remote_time_entry_ids = set(
                        map(lambda d: d.time_entries[0].id, time_entry_dataset)
                    )
                    local_time_entry_ids = set(
                        TimeEntry.objects(workspace=workspace).scalar("time_entry_id")
                    )
                    time_entry_ids_to_delete = (
                        local_time_entry_ids - remote_time_entry_ids
                    )
                    TimeEntry.delete_via_ids(time_entry_ids_to_delete)
                    time_entries_deleted += len(time_entry_ids_to_delete)

                    # delete tags
                    remote_tag_ids = set(map(lambda d: d.id, tag_dataset))
                    local_tag_ids = set(
                        Tag.objects(workspace=workspace).scalar("tag_id")
                    )
                    tag_ids_to_delete = local_tag_ids - remote_tag_ids
                    Tag.delete_via_ids(tag_ids_to_delete)
                    tags_deleted += len(tag_ids_to_delete)

                    # delete projects
                    remote_project_ids = set(map(lambda d: d.id, project_dataset))
                    local_project_ids = set(
                        Project.objects(workspace=workspace).scalar("project_id")
                    )
                    project_ids_to_delete = local_project_ids - remote_project_ids
                    Project.delete_via_ids(project_ids_to_delete)
                    projects_deleted += len(project_ids_to_delete)

                    # delete clients
                    remote_client_ids = set(map(lambda d: d.id, client_dataset))
                    local_client_ids = set(
                        Client.objects(workspace=workspace).scalar("client_id")
                    )
                    client_ids_to_delete = local_client_ids - remote_client_ids
                    Client.delete_via_ids(client_ids_to_delete)
                    clients_deleted += len(client_ids_to_delete)

            # delete workspaces
            used_workspace_ids = set()
            users = User.objects().only("workspaces")
            for user in users:
                used_workspace_ids.update(
                    map(lambda uw: uw.workspace.workspace_id, user.workspaces)
                )
            all_workspace_ids = set(Workspace.objects().scalar("workspace_id"))
            workspace_ids_to_delete = all_workspace_ids - used_workspace_ids
            Workspace.delete_via_ids(workspace_ids_to_delete)
            workspaces_deleted += len(workspace_ids_to_delete)

            # delete organizations
            used_organization_ids = set()
            workspaces = Workspace.objects().only("organization")
            for workspace in workspaces:
                used_organization_ids.update(
                    map(lambda w: w.organization.organization_id, workspaces)
                )
            all_organization_ids = set(Organization.objects().scalar("organization_id"))
            organization_ids_to_delete = all_organization_ids - used_organization_ids
            Organization.delete_via_ids(organization_ids_to_delete)
            organizations_deleted += len(organization_ids_to_delete)

            # log some sync stats
            logging.info("Users updated: %i", users_updated)
            logging.info(
                "Organizations created/updated: %i; deleted: %i",
                organizations_created_updated,
                organizations_deleted,
            )
            logging.info(
                "Workspaces created/updated: %i; deleted: %i",
                workspaces_created_updated,
                workspaces_deleted,
            )
            logging.info(
                "Clients created/updated: %i; deleted: %i",
                clients_created_updated,
                clients_deleted,
            )
            logging.info(
                "Projects created/updated: %i; deleted: %i",
                projects_created_updated,
                projects_deleted,
            )
            logging.info(
                "Tags created/updated: %i; deleted: %i",
                tags_created_updated,
                tags_deleted,
            )
            logging.info(
                "Time entries created/updated: %i; deleted %i",
                time_entries_created_updated,
                time_entries_deleted,
            )

    def sync_calendars(self):
        users = User.objects(next_calendar_sync_at__lte=datetime.now(timezone.utc))
        logging.info("Found %s users to sync with calendars", len(users))

        if len(users) > 0:
            schedules_created = 0
            schedules_updated = 0
            schedules_deleted = 0
            events_created = 0
            events_updated = 0
            events_deleted = 0

            cal_sync = CalendarSync()
            for user in users:
                for user_workspace in user.workspaces:
                    if user_workspace.schedule_calendar_url is not None:
                        # update user
                        user = cal_sync.update_user(
                            user, self.sync_interval_calendar, is_calendar_sync=True
                        )

                        # process ical file
                        workspace = user_workspace.workspace
                        ical = cal_sync.fetch_calendar(
                            user_workspace.schedule_calendar_url
                        )
                        components = cal_sync.filter_ical_components(ical)

                        # prepare schedules
                        schedules = cal_sync.get_existing_documents_with_uid(
                            Schedule, user, workspace
                        )
                        synced_schedule_uids = set()

                        # prepare events
                        events = cal_sync.get_existing_documents_with_uid(
                            Event, user, workspace
                        )
                        synced_event_uids = set()

                        for (
                            component,
                            annotation_type,
                            annotation_options,
                        ) in components:
                            match annotation_type:
                                # sync schedules
                                case cal_sync.TYPE_SCHEDULE:
                                    (
                                        schedule,
                                        created,
                                    ) = cal_sync.create_or_update_schedule(
                                        schedules,
                                        component,
                                        annotation_options,
                                        user,
                                        workspace,
                                    )
                                    if created:
                                        schedules_created += 1
                                    else:
                                        schedules_updated += 1
                                    synced_schedule_uids.add(schedule.source_uid)
                                    schedule.save()
                                # sync events
                                case cal_sync.TYPE_EVENT:
                                    event, created = cal_sync.create_or_update_event(
                                        events,
                                        component,
                                        annotation_options,
                                        user,
                                        workspace,
                                    )
                                    if created:
                                        events_created += 1
                                    else:
                                        events_updated += 1
                                    synced_event_uids.add(event.source_uid)
                                    event.save()

                        # delete schedules
                        schedules_to_delete = set(schedules.keys()).difference(
                            synced_schedule_uids
                        )
                        for schedule_uid in schedules_to_delete:
                            schedules[schedule_uid].delete()
                        schedules_deleted += len(schedules_to_delete)

                        # delete events
                        events_to_delete = set(events.keys()).difference(
                            synced_event_uids
                        )
                        for event_uid in events_to_delete:
                            events[event_uid].delete()
                        events_deleted += len(events_to_delete)

            # log some sync stats
            logging.info(
                "Schedules created: %i; updated: %i; deleted %i",
                schedules_created,
                schedules_updated,
                schedules_deleted,
            )
            logging.info(
                "Events created: %i; updated: %i; deleted %i",
                events_created,
                events_updated,
                events_deleted,
            )
