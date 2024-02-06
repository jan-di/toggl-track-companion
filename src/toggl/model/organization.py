from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class OrganizationData(ApiResource):
    """
    Represents a toggl organization (main api)
    https://developers.track.toggl.com/docs/organization
    https://developers.track.toggl.com/docs/api/organizations
    """

    at: str = None
    id: int = None
    name: str = None
    server_deleted_at: str = None
