from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class ProjectData(ApiResource):
    """
    Represents a toggl project (main api)
    https://developers.track.toggl.com/docs/projects
    https://developers.track.toggl.com/docs/api/projects
    """

    active: bool = None
    at: str = None
    color: str = None
    id: int = None
    name: str = None
    workspace_id: int = None
    client_id: int = None
