from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class WorkspaceData(ApiResource):
    """
    Represents a toggl workspace (main api)
    https://developers.track.toggl.com/docs/workspace
    https://developers.track.toggl.com/docs/api/workspaces
    """

    at: str = None
    id: int = None
    logo_url: str = None
    name: str = None
    organization_id: int = None
    server_deleted_at: str = None
