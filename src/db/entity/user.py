from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    DateField,
    DateTimeField,
    EmbeddedDocumentListField,
    ReferenceField,
    DoesNotExist,
)
from datetime import datetime, timezone, timedelta, date
import secrets

from src.db.entity.base_document import BaseDocument
from src.db.entity.workspace import Workspace
from src.toggl.model.me import MeData


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
