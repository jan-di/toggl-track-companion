from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class ClientData(ApiResource):
    """
    Represents a toggl client (main api)
    https://developers.track.toggl.com/docs/api/clients
    """

    archived: bool = None
    at: str = None
    id: int = None
    name: str = None
    server_deleted_at: str = None
    wid: int = None
