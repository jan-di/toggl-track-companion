from mongoengine import (
    Document,
    # EmbeddedDocument,
    StringField,
    IntField,
    DateTimeField
    # DateField,
    # EmbeddedDocumentField,
    # ListField,
    # FloatField,
)


# class UserCalendar(EmbeddedDocument):
#     url = StringField()
#     user_id = IntField(required=True)
#     organization_id = IntField(required=True)
#     workspace_id = IntField(required=True)


class User(Document):
    user_id = IntField(required=True)
    name = StringField(required=True)
    email = StringField(required=True)
    image_url = StringField()
    api_token = StringField(required=True)
    # calendars = ListField(EmbeddedDocumentField(UserCalendar))


class Organization(Document):
    fetched_at = DateTimeField(required=True)
    organization_id = IntField(required=True)
    name = StringField(required=True)


class Workspace(Document):
    fetched_at = DateTimeField(required=True)
    workspace_id = IntField(required=True)
    name = StringField(required=True)
