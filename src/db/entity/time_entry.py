from mongoengine import (
    StringField,
    IntField,
    DateTimeField,
    ListField,
    ReferenceField,
    DoesNotExist,
)
from datetime import datetime, timezone

from src.db.entity.base_document import BaseDocument
from src.db.entity.workspace import Workspace
from src.db.entity.user import User
from src.db.entity.project import Project
from src.db.entity.tag import Tag
from src.toggl.model import TimeEntryReportData


class TimeEntry(BaseDocument):
    COLLECTION_NAME = "time_entry"

    time_entry_id = IntField(primary_key=True, required=True)
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

    @classmethod
    def create_or_update_via_report_api_data(
        cls, time_entry_report_data: TimeEntryReportData, workspace_id: int
    ) -> "TimeEntry":
        try:
            time_entry = TimeEntry.objects.get(
                time_entry_id=time_entry_report_data.time_entries[0].id
            )
        except DoesNotExist:
            time_entry = TimeEntry()
            time_entry.time_entry_id = time_entry_report_data.time_entries[0].id
            time_entry.workspace = Workspace.to_dbref_pk(workspace_id)
            time_entry.user = User.to_dbref_pk(time_entry_report_data.user_id)

        start_dt = datetime.fromisoformat(time_entry_report_data.time_entries[0].start)
        stop_dt = datetime.fromisoformat(time_entry_report_data.time_entries[0].stop)

        time_entry.fetched_at = datetime.now(timezone.utc)
        time_entry.description = time_entry_report_data.description
        time_entry.started_at = start_dt
        time_entry.started_at_offset = start_dt.utcoffset().total_seconds()
        time_entry.stopped_at = stop_dt
        time_entry.stopped_at_offset = stop_dt.utcoffset().total_seconds()
        time_entry.project_id = Project.to_dbref_pk(time_entry_report_data.project_id)
        time_entry.tag_ids = Tag.to_dbref_pks(time_entry_report_data.tag_ids)

        return time_entry.save()

    @classmethod
    def delete_via_ids(cls, time_entry_ids: set) -> None:
        time_entries = TimeEntry.objects(time_entry_id__in=time_entry_ids)
        for time_entry in time_entries:
            time_entry.delete()
