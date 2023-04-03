from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    IntField,
    DateField,
    EmbeddedDocumentField,
    ListField,
)


class Calendar(EmbeddedDocument):
    url = StringField()
    user_id = IntField(required=True)
    organization_id = IntField(required=True)
    workspace_id = IntField(required=True)


class User(Document):
    name = StringField(required=True)
    username = StringField()
    calendars = ListField(EmbeddedDocumentField(Calendar))


class Schedule(Document):
    name = StringField(required=True)
    source_uid = StringField(required=True)
    start_date = DateField(required=True)
    rrule = StringField()
    user_id = IntField(required=True)
    organization_id = IntField(required=True)
    workspace_id = IntField(required=True)
    target = IntField(required=True)
