from mongoengine import (
    StringField,
    IntField,
    DateTimeField,
    ReferenceField,
    DoesNotExist,
)
from datetime import datetime, timezone

from src.db.entity.base_document import BaseDocument
from src.db.entity.workspace import Workspace
from src.db.entity.client import Client
from src.toggl.model import ProjectData


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
        for project in projects:
            project.delete()
