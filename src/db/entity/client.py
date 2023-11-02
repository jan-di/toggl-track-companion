from mongoengine import (
    StringField,
    IntField,
    DateTimeField,
    BooleanField,
    ReferenceField,
    DoesNotExist,
)
from datetime import datetime, timezone

from src.db.entity.base_document import BaseDocument
from src.db.entity.workspace import Workspace
from src.toggl.model import ClientData


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
        for client in clients:
            client.delete()
