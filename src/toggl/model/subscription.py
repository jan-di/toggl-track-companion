from dataclasses import dataclass, field

from src.toggl.model import ApiResource, EventFilterData


@dataclass
class SubscriptionData(ApiResource):
    """
    Represents a workspace subscription of the webhook api.
    https://developers.track.toggl.com/docs/webhooks/subscriptions
    """

    created_at: str = None
    deleted_at: str = None
    description: str = None
    enabled: bool = None
    event_filters: list[EventFilterData] = field(default_factory=list[EventFilterData])
    has_pending_events: bool = None
    secret: str = None
    subscription_id: int = None
    updated_at: str = None
    url_callback: str = None
    user_id: int = None
    validated_at: str = None
    workspace_id: int = None
