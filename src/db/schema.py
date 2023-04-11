from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    IntField,
    DateField,
    EmbeddedDocumentField,
    ListField,
    FloatField,
)


class UserCalendar(EmbeddedDocument):
    url = StringField()
    user_id = IntField(required=True)
    organization_id = IntField(required=True)
    workspace_id = IntField(required=True)


class User(Document):
    telegram_id = IntField(required=True)
    name = StringField(required=True)
    username = StringField()
    calendars = ListField(EmbeddedDocumentField(UserCalendar))


class Schedule(Document):
    name = StringField(required=True)
    source_uid = StringField(required=True)
    start_date = DateField(required=True)
    rrule = StringField()
    user_id = IntField(required=True)
    organization_id = IntField(required=True)
    workspace_id = IntField(required=True)
    target = IntField(required=True)


class Event(Document):
    name = StringField(required=True)
    source_uid = StringField(required=True)
    start_date = DateField(required=True)
    rrule = StringField()
    user_id = IntField(required=True)
    organization_id = IntField(required=True)
    workspace_id = IntField(required=True)
    factor = FloatField()
    addend = IntField()
