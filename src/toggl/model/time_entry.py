from dataclasses import dataclass, field

from src.toggl.model import ApiResource


@dataclass
class TimeEntryData(ApiResource):
    """
    Represents a toggl time entry (main api)
    https://developers.track.toggl.com/docs/tracking
    https://developers.track.toggl.com/docs/api/time_entries
    """

    at: str = None
    description: str = None
    id: int = None
    project_id: int = None
    server_deleted_at: str = None
    start: str = None
    stop: str = None
    tag_ids: list[int] = field(default_factory=list[int])
    user_id: int = None
    workspace_id: int = None

@dataclass
class SubTimeEntryReportData(ApiResource):
    """
    Represents the inner part of toggl time entry in a report (report api)
    https://developers.track.toggl.com/docs/reports/detailed_reports
    """

    at: str = None
    id: int = None
    start: str = None
    stop: str = None


@dataclass
class TimeEntryReportData(ApiResource):
    """
    Represents a toggl time entry in a report (report api)
    https://developers.track.toggl.com/docs/reports/detailed_reports
    """

    description: str = None
    project_id: int = None
    tag_ids: list[int] = field(default_factory=list[int])
    user_id: int = None
    time_entries: list[SubTimeEntryReportData] = field(
        default_factory=list[SubTimeEntryReportData]
    )
