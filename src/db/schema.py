from typing import Any
from bson import DBRef

from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    IntField,
    DateTimeField,
    # DateField,
    EmbeddedDocumentField,
    ListField,
    # FloatField,
    BooleanField,
    ReferenceField,
)


# class UserCalendar(EmbeddedDocument):
#     url = StringField()
#     user_id = IntField(required=True)
#     organization_id = IntField(required=True)
#     workspace_id = IntField(required=True)


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


class UserWorkspace(EmbeddedDocument):
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)


class User(BaseDocument):
    COLLECTION_NAME = "user"

    user_id = IntField(primary_key=True, required=True)
    default_workspace = ReferenceField(
        Workspace, db_field="default_workspace_id", required=True
    )
    workspaces = ListField(EmbeddedDocumentField(UserWorkspace))
    fetched_at = DateTimeField(required=True)
    next_sync_at = DateTimeField(required=True)
    name = StringField(required=True)
    email = StringField(required=True)
    image_url = StringField()
    api_token = StringField(required=True)

    meta = {"collection": COLLECTION_NAME}


class Client(BaseDocument):
    COLLECTION_NAME = "client"

    client_id = IntField(primary_key=True, required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)
    archived = BooleanField(required=True)

    meta = {"collection": COLLECTION_NAME}


class Project(BaseDocument):
    COLLECTION_NAME = "project"

    project_id = IntField(primary_key=True, required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    client = ReferenceField(Client, db_field="client_id")
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)
    color = StringField()

    meta = {"collection": COLLECTION_NAME}


class Tag(BaseDocument):
    COLLECTION_NAME = "tag"

    tag_id = IntField(primary_key=True, required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)

    meta = {"collection": COLLECTION_NAME}


class TimeEntry(BaseDocument):
    COLLECTION_NAME = "time_entry"

    time_entry_id = IntField(required=True, primary_key=True)
    user = ReferenceField(User, db_field="user_id", required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    project = ReferenceField(Project, db_field="project_id")
    tags = ListField(ReferenceField(Tag), db_field="tag_ids")
    fetched_at = DateTimeField(required=True)
    description = StringField(required=True)
    started_at = DateTimeField(required=True)
    started_at_offset = IntField(required=True)
    stopped_at = DateTimeField()
    stopped_at_offset = IntField()

    meta = {"collection": COLLECTION_NAME}
