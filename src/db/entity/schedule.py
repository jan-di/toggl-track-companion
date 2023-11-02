from mongoengine import (
    StringField,
    IntField,
    DateField,
    ReferenceField,
)

from src.db.entity.base_document import BaseDocument
from src.db.entity.workspace import Workspace
from src.db.entity.user import User


class Schedule(BaseDocument):
    source_uid = StringField(primary_key=True, required=True)
    user = ReferenceField(User, db_field="user_id", required=True)
    workspace = ReferenceField(Workspace, db_field="workspace_id", required=True)
    name = StringField(required=True)
    start_date = DateField(required=True)
    rrule = StringField()
    target = IntField(required=True)
