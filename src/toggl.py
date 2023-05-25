from datetime import datetime

import httpx
from mongoengine import DoesNotExist
from src.db.schema import User, Organization, Workspace


class TogglApi:
    def __init__(
        self,
        api_token: str = None,
        username: str = None,
        password: str = None,
        base_url: str = "https://api.track.toggl.com",
    ):
        self.api_token = api_token
        self.username = username
        self.password = password
        self.base_url = base_url
        self.client = httpx.Client()

    def get_me(self) -> tuple[bool, any, int]:
        req = self.__request("GET", "/api/v9/me")
        return self.__response(req)

    def get_my_organizations(self) -> tuple[bool, any, int]:
        req = self.__request("GET", "/api/v9/me/organizations")
        return self.__response(req)

    def get_my_workspaces(self) -> tuple[bool, any, int]:
        req = self.__request("GET", "/api/v9/me/all_workspaces")
        return self.__response(req)

    # def get_time_entries(self, since=None, start_date=None, end_date=None):
    #     params = {}
    #     if since is not None:
    #         params["since"] = since
    #     if start_date is not None:
    #         params["start_date"] = start_date
    #     if end_date is not None:
    #         params["end_date"] = end_date

    #     req = self.__request("GET", "/api/v9/me/time_entries", params)
    #     data = req.json()
    #     return list(map(self.__create_time_entry_from_api, data))

    def __request(
        self, method: str, endpoint: str, params: dict = None
    ) -> httpx.Request:
        if params is None:
            params = {}

        if self.api_token:
            auth = (self.api_token, "api_token")
        else:
            auth = (self.username, self.password)

        req = self.client.request(
            method=method,
            params=params,
            url=f"{self.base_url}{endpoint}",
            auth=auth,
        )

        return req

    def __response(self, request: httpx.Request) -> tuple[bool, any, int]:
        success = request.status_code < 300
        if success and request.headers.get("content-type").lower().startswith(
            "application/json"
        ):
            data = request.json()
        else:
            data = request.text
        status = request.status_code

        return success, data, status

    # def __create_user_from_api(self, data: map) -> User:
    #     return User(
    #         id=data["id"],
    #         fullname=data["fullname"],
    #         email=data["email"],
    #         country_id=data["country_id"],
    #         timezone=data["timezone"],
    #         beginning_of_week=data["beginning_of_week"],
    #         image_url=data["image_url"],
    #         created_at=data["created_at"],
    #         updated_at=data["at"],
    #         api_token=data["api_token"],
    #     )

    # def __create_organization_from_api(self, data: map) -> Organization:
    #     return Organization(
    #         id=data["id"],
    #         name=data["name"],
    #         created_at=data["created_at"],
    #         updated_at=data["at"],
    #         deleted_at=data["server_deleted_at"],
    #     )

    # def __create_workspace_from_api(self, data: map) -> Workspace:
    #     return Workspace(
    #         id=data["id"],
    #         organization_id=data["organization_id"],
    #         name=data["name"],
    #         updated_at=data["at"],
    #         deleted_at=data["server_deleted_at"],
    #         logo_url=data["logo_url"],
    #     )

    # def __create_time_entry_from_api(self, data: map) -> TimeEntry:
    #     return TimeEntry(
    #         id=data["id"],
    #         description=data["description"],
    #         start=data["start"],
    #         stop=data["stop"],
    #         updated_at=data["at"],
    #         user_id=data["user_id"],
    #         workspace_id=data["workspace_id"],
    #     )


class TogglUpdater:
    def create_or_update_user(self, user_data: dict) -> User:
        try:
            user = User.objects.get(user_id=user_data["id"])
        except DoesNotExist:
            user = User()
            user.user_id = user_data["id"]
        
        user.name = user_data["fullname"]
        user.email = user_data["email"]
        user.image_url = user_data["image_url"]
        user.api_token = user_data["api_token"]

        user.save()

        return user

    def create_or_update_organization(self, organization_data: dict) -> Organization:
        try:
            organization = Organization.objects.get(
                organization_id=organization_data["id"]
            )
        except DoesNotExist:
            organization = Organization()
            organization.organization_id = organization_data["id"]

        organization.fetched_at = datetime.now
        organization.name = organization_data["name"]

        organization.save()

        return organization

    def create_or_update_workspace(self, workspace_data: dict) -> Workspace:
        try:
            workspace = Workspace.objects.get(workspace_id=workspace_data["id"])
        except DoesNotExist:
            workspace = Workspace()
            workspace.workspace_id = workspace_data["id"]

        workspace.fetched_at = datetime.now
        workspace.name = workspace_data["name"]

        workspace.save()

        return workspace
