from dataclasses import dataclass

from src.toggl.model import ApiResource


@dataclass
class EventFilterData(ApiResource):
    """
    Represets a toggl event filter resource (webhook api).
    https://developers.track.toggl.com/docs/webhooks_start/event_filters
    https://developers.track.toggl.com/docs/webhooks/event_filters
    """

    action: str = None
    entity: str = None
