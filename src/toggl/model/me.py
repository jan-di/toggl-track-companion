from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class MeData(ApiResource):
    """
    Represents me (user) (main api).
    https://developers.track.toggl.com/docs/api/me
    """

    api_token: str = None
    at: str = None
    beginning_of_week: str = None
    id: int = None
    email: str = None
    fullname: str = None
    image_url: str = None
    timezone: str = None
