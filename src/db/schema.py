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
)


# class UserCalendar(EmbeddedDocument):
#     url = StringField()
#     user_id = IntField(required=True)
#     organization_id = IntField(required=True)
#     workspace_id = IntField(required=True)


class UserWorkspace(EmbeddedDocument):
    workspace_id = IntField(required=True)


class User(Document):
    user_id = IntField(required=True)
    fetched_at = DateTimeField(required=True)
    next_sync_at = DateTimeField(required=True)
    name = StringField(required=True)
    email = StringField(required=True)
    image_url = StringField()
    api_token = StringField(required=True)
    default_workspace_id = IntField(required=True)
    workspaces = ListField(EmbeddedDocumentField(UserWorkspace))
    # calendars = ListField(EmbeddedDocumentField(UserCalendar))

    meta = {"indexes": ["user_id"]}


class Organization(Document):
    fetched_at = DateTimeField(required=True)
    organization_id = IntField(required=True)
    name = StringField(required=True)

    meta = {"indexes": ["organization_id"]}


class Workspace(Document):
    fetched_at = DateTimeField(required=True)
    workspace_id = IntField(required=True)
    organization_id = IntField(required=True)
    name = StringField(required=True)
    logo_url = StringField()

    meta = {"indexes": ["workspace_id", "organization_id"]}


class TimeEntry(Document):
    fetched_at = DateTimeField(required=True)
    time_entry_id = IntField(required=True)
    user_id = IntField(required=True)
    workspace_id = IntField(required=True)
    project_id = IntField()
    tag_ids = ListField(IntField())
    description = StringField(required=True)
    started_at = DateTimeField(required=True)
    started_at_offset = IntField(required=True)
    stopped_at = DateTimeField()
    stopped_at_offset = IntField(required=True)

    meta = {
        "indexes": ["time_entry_id", "user_id", "workspace_id", "project_id", "tag_ids"]
    }


class Client(Document):
    fetched_at = DateTimeField(required=True)
    client_id = IntField(required=True)
    workspace_id = IntField(required=True)
    name = StringField(required=True)
    archived = BooleanField(required=True)

    meta = {"indexes": ["client_id", "workspace_id"]}


class Project(Document):
    fetched_at = DateTimeField(required=True)
    project_id = IntField(required=True)
    workspace_id = IntField(required=True)
    name = StringField(required=True)
    color = StringField()

    meta = {"indexes": ["project_id", "workspace_id"]}


class Tag(Document):
    fetched_at = DateTimeField(required=True)
    tag_id = IntField(required=True)
    workspace_id = IntField(required=True)
    name = StringField(required=True)

    meta = {"indexes": ["tag_id", "workspace_id"]}
