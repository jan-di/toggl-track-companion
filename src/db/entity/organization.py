from mongoengine import (
    StringField,
    IntField,
    DateTimeField,
    DoesNotExist,
)
from datetime import datetime, timezone

from src.db.entity.base_document import BaseDocument
from src.toggl.model import OrganizationData


class Organization(BaseDocument):
    COLLECTION_NAME = "organization"

    organization_id = IntField(primary_key=True, required=True)
    fetched_at = DateTimeField(required=True)
    name = StringField(required=True)

    meta = {"collection": COLLECTION_NAME}

    @classmethod
    def create_or_update_via_api_data(
        cls, organization_data: OrganizationData
    ) -> "Organization":
        try:
            organization = Organization.objects.get(
                organization_id=organization_data.id
            )
        except DoesNotExist:
            organization = Organization(organization_id=organization_data.id)

        organization.fetched_at = datetime.now(timezone.utc)
        organization.name = organization_data.name

        return organization.save()

    @classmethod
    def delete_via_ids(cls, organization_ids: set) -> None:
        organizations = Organization.objects(organization_id__in=organization_ids)
        for organization in organizations:
            organization.delete()
