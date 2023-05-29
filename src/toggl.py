from datetime import datetime, timedelta, date
import time

import httpx
from mongoengine import DoesNotExist
from src.db.schema import (
    User,
    UserWorkspace,
    Organization,
    Workspace,
    TimeEntry,
    Client,
    Tag,
    Project,
)


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

    def get_me(self) -> dict:
        return self.__simple_request("GET", "/api/v9/me")

    def get_my_organizations(self) -> list[dict]:
        return self.__simple_request("GET", "/api/v9/me/organizations")

    def get_my_workspaces(self) -> list[dict]:
        return self.__simple_request("GET", "/api/v9/me/all_workspaces")

    def get_workspace_clients(self, workspace_id: int) -> list[dict]:
        return self.__simple_request(
            "GET", f"/api/v9/workspaces/{workspace_id}/clients"
        )

    def get_workspace_tags(self, workspace_id: int) -> list[dict]:
        return self.__simple_request("GET", f"/api/v9/workspaces/{workspace_id}/tags")

    def get_workspace_projects(self, workspace_id: int) -> list[dict]:
        return self.__paginated_request(
            "GET", f"/api/v9/workspaces/{workspace_id}/projects"
        )

    def get_workspace_time_entries(
        self, workspace_id: int, start_date: date, end_date: date
    ) -> list:
        body = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        return self.__paginated_report_request(
            "POST",
            f"/reports/api/v3/workspace/{workspace_id}/search/time_entries",
            body,
        )

    def __request(
        self, method: str, endpoint: str, params: dict = None, json_body: dict = None
    ) -> httpx.Request:
        if params is None:
            params = {}

        if self.api_token:
            auth = (self.api_token, "api_token")
        else:
            auth = (self.username, self.password)

        response = self.client.request(
            method=method,
            params=params,
            url=f"{self.base_url}{endpoint}",
            json=json_body,
            auth=auth,
        )
        response.raise_for_status()
        time.sleep(0.5)

        return response

    def __simple_request(self, method: str, endpoint: str, params: dict = None):
        response = self.__request(method, endpoint, params=params)

        return response.json()

    def __paginated_request(self, method: str, endpoint: str, params: dict = None):
        result = []
        params = {} if params is None else params
        params["page"] = 1

        while True:
            response = self.__request(method, endpoint, params=params)
            response_json = response.json()

            if len(response_json) == 0:
                break

            result += response_json
            params["page"] += 1

        return result

    def __paginated_report_request(
        self, method: str, endpoint: str, json_body: dict = None
    ):
        result = []
        json_body = {} if json_body is None else json_body

        while True:
            response = self.__request(method, endpoint, json_body=json_body)
            result += response.json()

            if "x-next-row-number" in response.headers:
                json_body["first_row_number"] = int(
                    response.headers["x-next-row-number"]
                )
            else:
                break

        return result


class TogglUpdater:
    MIN_YEAR = 2006

    def create_or_update_user_from_api(
        self, user_data: dict, next_sync: int = 0
    ) -> User:
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
        user.default_workspace_id = user_data["default_workspace_id"]

        return user.save()

    def update_user_workspaces_from_api(
        self, user: User, workspace_dataset: list
    ) -> User:
        user.workspaces = list(
            map(lambda w: UserWorkspace(workspace_id=w["id"]), workspace_dataset)
        )

        return user.save()

    def create_or_update_organization_from_api(
        self, organization_data: dict
    ) -> Organization:
        try:
            organization = Organization.objects.get(
                organization_id=organization_data["id"]
            )
        except DoesNotExist:
            organization = Organization(organization_id=organization_data["id"])

        organization.fetched_at = datetime.now()
        organization.name = organization_data["name"]

        return organization.save()

    def delete_organizations_via_ids(self, organization_ids: set) -> None:
        organizations = Organization.objects(organization_id__in=organization_ids)
        for organization in organizations:
            organization.delete()

    def create_or_update_workspace_from_api(self, workspace_data: dict) -> Workspace:
        try:
            workspace = Workspace.objects.get(
                workspace_id=workspace_data["id"],
            )
        except DoesNotExist:
            workspace = Workspace(
                workspace_id=workspace_data["id"],
                organization_id=workspace_data["organization_id"],
            )

        workspace.fetched_at = datetime.now()
        workspace.name = workspace_data["name"]
        workspace.logo_url = workspace_data["logo_url"]

        return workspace.save()

    def delete_workspaces_via_ids(self, workspace_ids: set) -> None:
        workspaces = Workspace.objects(workspace_id__in=workspace_ids)
        for workspace in workspaces:
            workspace.delete()

    def create_or_update_time_entry_from_report_api(
        self, time_entry_data: dict, workspace_id: int
    ) -> TimeEntry:
        try:
            time_entry = TimeEntry.objects.get(
                time_entry_id=time_entry_data["time_entries"][0]["id"]
            )
        except DoesNotExist:
            time_entry = TimeEntry()
            time_entry.time_entry_id = time_entry_data["time_entries"][0]["id"]
            time_entry.workspace_id = workspace_id
            time_entry.user_id = time_entry_data["user_id"]

        start_dt = datetime.fromisoformat(time_entry_data["time_entries"][0]["start"])
        stop_dt = datetime.fromisoformat(time_entry_data["time_entries"][0]["stop"])

        time_entry.fetched_at = datetime.now()
        time_entry.description = time_entry_data["description"]
        time_entry.started_at = start_dt
        time_entry.started_at_offset = start_dt.utcoffset().total_seconds()
        time_entry.stopped_at = stop_dt
        time_entry.stopped_at_offset = stop_dt.utcoffset().total_seconds()
        time_entry.project_id = time_entry_data["project_id"]
        time_entry.tag_ids = time_entry_data["tag_ids"]

        return time_entry.save()

    def delete_time_entries_via_ids(self, time_entry_ids: set) -> None:
        time_entries = TimeEntry.objects(time_entry_id__in=time_entry_ids)
        for time_entry in time_entries:
            time_entry.delete()

    def create_or_update_client_from_api(self, client_data: dict) -> Client:
        try:
            client = Client.objects.get(client_id=client_data["id"])
        except DoesNotExist:
            client = Client(
                client_id=client_data["id"],
                workspace_id=client_data["wid"],
            )

        client.fetched_at = datetime.now()
        client.name = client_data["name"]
        client.archived = client_data["archived"]

        return client.save()

    def delete_clients_via_ids(self, client_ids: set) -> None:
        clients = Client.objects(client_id__in=client_ids)
        for client in clients:
            client.delete()

    def create_or_update_project_from_api(self, project_data: dict) -> Project:
        try:
            project = Project.objects.get(project_id=project_data["id"])
        except DoesNotExist:
            project = Project(
                project_id=project_data["id"],
                workspace_id=project_data["workspace_id"],
            )

        project.fetched_at = datetime.now()
        project.name = project_data["name"]
        project.color = project_data["color"]

        return project.save()

    def delete_projects_via_ids(self, project_ids: set) -> None:
        projects = Project.objects(project_id__in=project_ids)
        for project in projects:
            project.delete()

    def create_or_update_tag_from_api(self, tag_data: dict) -> Tag:
        try:
            tag = Tag.objects.get(tag_id=tag_data["id"])
        except DoesNotExist:
            tag = Tag(
                tag_id=tag_data["id"],
                workspace_id=tag_data["workspace_id"],
            )

        tag.fetched_at = datetime.now()
        tag.name = tag_data["name"]

        return tag.save()

    def delete_tags_via_ids(self, tag_ids: set) -> None:
        tags = Tag.objects(tag_id__in=tag_ids)
        for tag in tags:
            tag.delete()
