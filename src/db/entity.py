from datetime import datetime, timezone, timedelta, date
from bson import DBRef
from typing import Any
import secrets

from mongoengine import (
    Document,
    BooleanField,
    DateField,
    DateTimeField,
    DoesNotExist,
    EmbeddedDocument,
    EmbeddedDocumentListField,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from src.toggl.model.me import MeData
from src.toggl.model import (
    WorkspaceData,
    ClientData,
    ProjectData,
    OrganizationData,
    TagData,
    TimeEntryData,
    TimeEntryReportData,
)


class BaseDocument(Document):
    COLLECTION_NAME = ""

    @classmethod
    def to_dbref_pk(cls, primary_key: Any | None):
        return (
            DBRef(cls.COLLECTION_NAME, primary_key) if primary_key is not None else None
        )

    @classmethod
    def to_dbref_pks(cls, primary_keys: list[Any] | None):
        return (
            list(map(cls.to_dbref_pk, primary_keys))
            if primary_keys is not None
            else None
        )

    meta = {"abstract": True}


class Organization(BaseDocument):
    COLLECTION_NAME = "organization"

    organization_id = IntField(primary_key=True, required=True)
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(
        cls, organization_data: OrganizationData
    ) -> "Organization":
        try:
            organization = Organization.objects.get(
                organization_id=organization_data.id
            )
        except DoesNotExist:
            organization = Organization(organization_id=organization_data.id)

        organization.fetched_at = datetime.now(timezone.utc)
        organization.name = organization_data.name

        return organization.save()

    @classmethod
    def delete_via_ids(cls, organization_ids: set) -> None:
        organizations = Organization.objects(organization_id__in=organization_ids)
        for organization in organizations:
            organization.delete()


class Workspace(BaseDocument):
    COLLECTION_NAME = "workspace"

    workspace_id = IntField(primary_key=True, required=True)
    organization = ReferenceField(
        Organization, db_field="organization_id", required=True
    )
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)
    logo_url = StringField()

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(
        cls, workspace_data: WorkspaceData
    ) -> "Workspace":
        try:
            workspace = Workspace.objects.get(
                workspace_id=workspace_data.id,
            )
        except DoesNotExist:
            workspace = Workspace(
                workspace_id=workspace_data.id,
                organization=Organization.to_dbref_pk(workspace_data.organization_id),
            )

        workspace.fetched_at = datetime.now(timezone.utc)
        workspace.name = workspace_data.name
        workspace.logo_url = workspace_data.logo_url

        return workspace.save()

    @classmethod
    def delete_via_ids(cls, workspace_ids: set) -> None:
        workspaces = Workspace.objects(workspace_id__in=workspace_ids)
        for workspace in workspaces:
            workspace.delete()


class UserWorkspace(EmbeddedDocument):
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    schedule_calendar_url = StringField()
    start_of_aggregation = DateField(required=True)
    subscription_token = StringField()
    last_webhook_event_received_at = DateTimeField()


class User(BaseDocument):
    COLLECTION_NAME = "user"

    user_id = IntField(primary_key=True, required=True)
    default_workspace = ReferenceField(Workspace, db_field="default_workspace_id")
    workspaces = EmbeddedDocumentListField(UserWorkspace)
    fetched_at = DateTimeField(required=True)
    next_calendar_sync_at = DateTimeField(required=True)
    last_calendar_sync_at = DateTimeField()
    next_toggl_sync_at = DateTimeField(required=True)
    last_toggl_sync_at = DateTimeField()
    name = StringField(required=True)
    email = StringField(required=True)
    image_url = StringField()
    api_token = StringField(required=True)
    timezone = StringField(required=True)

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(
        cls, me_data: MeData, next_toggl_sync: int = 0, is_toggl_sync=False
    ) -> "User":
        try:
            user = User.objects.get(user_id=me_data.id)
        except DoesNotExist:
            user = User()
            user.user_id = me_data.id
            user.next_calendar_sync_at = datetime.now(timezone.utc)

        user.next_toggl_sync_at = datetime.now(timezone.utc) + timedelta(
            seconds=next_toggl_sync
        )
        if is_toggl_sync:
            user.last_toggl_sync_at = datetime.now(timezone.utc)

        user.fetched_at = datetime.now(timezone.utc)
        user.name = me_data.fullname
        user.email = me_data.email
        user.image_url = me_data.image_url
        user.api_token = me_data.api_token
        user.timezone = me_data.timezone

        return user.save()

    @classmethod
    def update_workspaces_via_api_data(
        cls, user: "User", workspace_dataset: list
    ) -> "User":
        indexed_workspace_dataset = {wd.id: wd for wd in workspace_dataset}
        indexed_workspaces = {w.workspace.id: w for w in user.workspaces}
        keys_to_delete = set(indexed_workspaces.keys()) - set(
            indexed_workspace_dataset.keys()
        )
        keys_to_add = set(indexed_workspace_dataset.keys()) - set(
            indexed_workspaces.keys()
        )

        for key in keys_to_delete:
            del indexed_workspaces[key]

        for key in keys_to_add:
            indexed_workspaces[key] = UserWorkspace(
                workspace=Workspace.to_dbref_pk(key)
            )
            indexed_workspaces[key].start_of_aggregation = date.today()

        for workspace in indexed_workspaces.values():
            if (
                workspace.subscription_token is None
                or len(workspace.subscription_token) == 0
            ):
                workspace.subscription_token = secrets.token_hex(32)

        user.workspaces = list(indexed_workspaces.values())

        return user.save()


class Client(BaseDocument):
    COLLECTION_NAME = "client"

    client_id = IntField(primary_key=True, required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)
    archived = BooleanField(required=True)

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(cls, client_data: ClientData) -> "Client":
        try:
            client = Client.objects.get(client_id=client_data.id)
        except DoesNotExist:
            client = Client(
                client_id=client_data.id,
                workspace=Workspace.to_dbref_pk(client_data.wid),
            )

        client.fetched_at = datetime.now(timezone.utc)
        client.name = client_data.name
        client.archived = client_data.archived

        return client.save()

    @classmethod
    def delete_via_ids(cls, client_ids: set) -> None:
        clients = Client.objects(client_id__in=client_ids)

        for project in Project.objects(client__in=clients):
            project.client = None
            project.save()

        for client in clients:
            client.delete()

    @classmethod
    def delete_via_id(cls, client_id: int) -> None:
        cls.delete_via_ids((client_id,))


class Project(BaseDocument):
    COLLECTION_NAME = "project"

    project_id = IntField(primary_key=True, required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    client = ReferenceField(Client, db_field="client_id")
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)
    color = StringField()

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(cls, project_data: ProjectData) -> "Project":
        try:
            project = Project.objects.get(project_id=project_data.id)
        except DoesNotExist:
            project = Project(
                project_id=project_data.id,
                workspace=Workspace.to_dbref_pk(project_data.workspace_id),
            )

        project.fetched_at = datetime.now(timezone.utc)
        project.name = project_data.name
        project.color = project_data.color
        project.client = Client.to_dbref_pk(project_data.client_id)

        return project.save()

    @classmethod
    def delete_via_ids(cls, project_ids: set) -> None:
        projects = Project.objects(project_id__in=project_ids)

        for time_entry in TimeEntry.objects(project__in=projects):
            time_entry.project = None
            time_entry.save()

        for project in projects:
            project.delete()

    @classmethod
    def delete_via_id(cls, project_id: int) -> None:
        cls.delete_via_ids((project_id,))


class Tag(BaseDocument):
    COLLECTION_NAME = "tag"

    tag_id = IntField(primary_key=True, required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(cls, tag_data: TagData) -> "Tag":
        try:
            tag = Tag.objects.get(tag_id=tag_data.id)
        except DoesNotExist:
            tag = Tag(
                tag_id=tag_data.id,
                workspace=Workspace.to_dbref_pk(tag_data.workspace_id),
            )

        tag.fetched_at = datetime.now(timezone.utc)
        tag.name = tag_data.name

        return tag.save()

    @classmethod
    def delete_via_ids(cls, tag_ids: set) -> None:
        tags = Tag.objects(tag_id__in=tag_ids)
        for tag in tags:
            tag.delete()

    @classmethod
    def delete_via_id(cls, tag_id: int) -> None:
        cls.delete_via_ids((tag_id,))


class Event(BaseDocument):
    source_uid = StringField(primary_key=True, required=True)
    user = ReferenceField(User, db_field="user_id", required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    name = StringField(required=True)
    start_date = DateField(required=True)
    rrule = StringField()
    mod_relative = FloatField(required=True)
    mod_absolute = IntField(required=True)


class Schedule(BaseDocument):
    source_uid = StringField(primary_key=True, required=True)
    user = ReferenceField(User, db_field="user_id", required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    name = StringField(required=True)
    start_date = DateField(required=True)
    rrule = StringField()
    target = IntField(required=True)


class TimeEntry(BaseDocument):
    COLLECTION_NAME = "time_entry"

    time_entry_id = IntField(primary_key=True, required=True)
    user = ReferenceField(User, db_field="user_id", required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    project = ReferenceField(Project, db_field="project_id")
    tags = ListField(ReferenceField(Tag), db_field="tag_ids")
    fetched_at = DateTimeField(required=True)
    description = StringField(required=True)
    started_at = DateTimeField(required=True)
    stopped_at = DateTimeField()

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(
        cls, time_entry_data: TimeEntryData
    ) -> "TimeEntry":
        try:
            time_entry = TimeEntry.objects.get(time_entry_id=time_entry_data.id)
        except DoesNotExist:
            time_entry = TimeEntry()
            time_entry.time_entry_id = time_entry_data.id
            time_entry.workspace = Workspace.to_dbref_pk(time_entry_data.workspace_id)
            time_entry.user = User.to_dbref_pk(time_entry_data.user_id)

        time_entry.fetched_at = datetime.now(timezone.utc)
        time_entry.description = time_entry_data.description
        time_entry.started_at = datetime.fromisoformat(time_entry_data.start)
        if time_entry_data.stop is not None:
            time_entry.stopped_at = datetime.fromisoformat(time_entry_data.stop)
        else:
            time_entry.stopped_at = None
        time_entry.project_id = Project.to_dbref_pk(time_entry_data.project_id)
        time_entry.tag_ids = Tag.to_dbref_pks(time_entry_data.tag_ids)

        return time_entry.save()

    @classmethod
    def create_or_update_via_report_api_data(
        cls, time_entry_report_data: TimeEntryReportData, workspace_id: int
    ) -> "TimeEntry":
        try:
            time_entry = TimeEntry.objects.get(
                time_entry_id=time_entry_report_data.time_entries[0].id
            )
        except DoesNotExist:
            time_entry = TimeEntry()
            time_entry.time_entry_id = time_entry_report_data.time_entries[0].id
            time_entry.workspace = Workspace.to_dbref_pk(workspace_id)
            time_entry.user = User.to_dbref_pk(time_entry_report_data.user_id)

        # Time Entries from a report does always have a start and stop time set
        start_dt = datetime.fromisoformat(time_entry_report_data.time_entries[0].start)
        stop_dt = datetime.fromisoformat(time_entry_report_data.time_entries[0].stop)

        time_entry.fetched_at = datetime.now(timezone.utc)
        time_entry.description = time_entry_report_data.description
        time_entry.started_at = start_dt
        time_entry.stopped_at = stop_dt
        time_entry.project_id = Project.to_dbref_pk(time_entry_report_data.project_id)
        time_entry.tag_ids = Tag.to_dbref_pks(time_entry_report_data.tag_ids)

        return time_entry.save()

    @classmethod
    def delete_via_ids(cls, time_entry_ids: set) -> None:
        time_entries = TimeEntry.objects(time_entry_id__in=time_entry_ids)
        for time_entry in time_entries:
            time_entry.delete()

    @classmethod
    def delete_via_id(cls, time_entry_id: int) -> None:
        cls.delete_via_ids((time_entry_id,))
