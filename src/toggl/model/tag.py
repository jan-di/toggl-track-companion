from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class TagData(ApiResource):
    """
    Represents a tag (main api).
    https://developers.track.toggl.com/docs/tags
    https://developers.track.toggl.com/docs/api/tags
    """

    at: str = None
    deleted_at: str = None
    id: int = None
    name: str = None
    workspace_id: int = None
