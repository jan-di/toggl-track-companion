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
from src.toggl.model import TagData


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
