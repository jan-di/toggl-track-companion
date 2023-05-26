from datetime import datetime, timedelta, date
import time

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

    def get_me(self) -> tuple[bool, any]:
        req = self.__request("GET", "/api/v9/me")
        return self.__response(req)

    def get_my_organizations(self) -> tuple[bool, any]:
        req = self.__request("GET", "/api/v9/me/organizations")
        return self.__response(req)

    def get_my_workspaces(self) -> tuple[bool, any]:
        req = self.__request("GET", "/api/v9/me/all_workspaces")
        return self.__response(req)
    
    def search_time_entries(self, workspace_id: int, start_date: date, end_date: date) -> list:
        body = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        result = []

        while True:
            response = self.__request("POST", f"/reports/api/v3/workspace/{workspace_id}/search/time_entries", json_body=body)
            response.raise_for_status()
            result += response.json()

            if "x-next-row-number" in response.headers:
                body["first_row_number"] = int(response.headers["x-next-row-number"])
            else:
                break

        return result

    def __request(
        self, method: str, endpoint: str, params: dict = None, json_body: dict = None
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
            json=json_body,
            auth=auth,
        )
        time.sleep(0.5)

        return req

    def __response(self, request: httpx.Request) -> tuple[bool, any, int]:
        success = request.status_code < 300
        if success and request.headers.get("content-type").lower().startswith(
            "application/json"
        ):
            data = request.json()
        else:
            data = request.text

        return success, data


class TogglUpdater:
    MIN_YEAR = 2006

    def create_or_update_user(self, user_data: dict, next_sync: int = 0) -> User:
        try:
            user = User.objects.get(user_id=user_data["id"])
            user.next_sync_at = datetime.now() + timedelta(seconds=next_sync)
        except DoesNotExist:
            user = User()
            user.user_id = user_data["id"]
            user.next_sync_at = datetime.now()
        
        user.fetched_at = datetime.now()
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

        organization.fetched_at = datetime.now()
        organization.name = organization_data["name"]

        organization.save()

        return organization

    def create_or_update_workspace(self, workspace_data: dict) -> Workspace:
        try:
            workspace = Workspace.objects.get(workspace_id=workspace_data["id"])
        except DoesNotExist:
            workspace = Workspace()
            workspace.workspace_id = workspace_data["id"]

        workspace.fetched_at = datetime.now()
        workspace.name = workspace_data["name"]

        workspace.save()

        return workspace
