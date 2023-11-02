from mongoengine import (
    StringField,
    IntField,
    DateTimeField,
    ReferenceField,
    DoesNotExist,
)
from datetime import datetime, timezone

from src.db.entity.base_document import BaseDocument
from src.db.entity.organization import Organization
from src.toggl.model import WorkspaceData


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
