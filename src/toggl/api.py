import httpx
import time
from datetime import date

from src.toggl.model import (
    TagData,
    MeData,
    OrganizationData,
    WorkspaceData,
    ClientData,
    ProjectData,
    SubscriptionData,
    TimeEntryReportData,
)


class TogglApi:
    MIN_YEAR = 2006

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

    def get_me(
        self,
    ) -> MeData:
        response_body = self.__simple_request(
            "GET",
            "/api/v9/me",
        )
        return MeData.from_dict(response_body)

    def get_my_organizations(
        self,
    ) -> list[OrganizationData]:
        response_body = self.__simple_request(
            "GET",
            "/api/v9/me/organizations",
        )
        return OrganizationData.from_dict_list(response_body)

    def get_my_workspaces(
        self,
    ) -> list[WorkspaceData]:
        response_body = self.__simple_request(
            "GET",
            "/api/v9/me/workspaces",
        )
        return WorkspaceData.from_dict_list(response_body)

    def get_workspace_clients(
        self,
        workspace_id: int,
    ) -> list[ClientData]:
        response_body = (
            self.__simple_request(
                "GET",
                f"/api/v9/workspaces/{workspace_id}/clients",
            )
            or []
        )
        return ClientData.from_dict_list(response_body)

    def get_workspace_tags(
        self,
        workspace_id: int,
    ) -> list[TagData]:
        response_body = (
            self.__simple_request(
                "GET",
                f"/api/v9/workspaces/{workspace_id}/tags",
            )
            or []
        )
        return WorkspaceData.from_dict_list(response_body)

    def get_workspace_projects(
        self,
        workspace_id: int,
    ) -> list[ProjectData]:
        response_body = self.__paginated_request(
            "GET",
            f"/api/v9/workspaces/{workspace_id}/projects",
        )
        return ProjectData.from_dict_list(response_body)

    def get_workspace_subscriptions(
        self,
        workspace_id: int,
    ) -> list[SubscriptionData]:
        response_body = self.__simple_request(
            "GET",
            f"/webhooks/api/v1/subscriptions/{workspace_id}",
        )

        return SubscriptionData.from_dict_list(response_body)

    def create_workspace_subscription(
        self,
        workspace_id: int,
        subscription: SubscriptionData,
    ) -> None:
        self.__simple_request(
            "POST",
            f"/webhooks/api/v1/subscriptions/{workspace_id}",
            json_body=subscription.to_dict(),
        )

    def get_workspace_time_entry_report_start_end(
        self, workspace_id: int, start_date: date, end_date: date
    ) -> list[TimeEntryReportData]:
        request_body = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        response_body = self.__paginated_report_request(
            "POST",
            f"/reports/api/v3/workspace/{workspace_id}/search/time_entries",
            request_body,
        )
        return TimeEntryReportData.from_dict_list(response_body)

    def __http_request(
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

    def __simple_request(
        self, method: str, endpoint: str, params: dict = None, json_body: dict = None
    ):
        response = self.__http_request(
            method, endpoint, params=params, json_body=json_body
        )

        return response.json()

    def __paginated_request(self, method: str, endpoint: str, params: dict = None):
        result = []
        params = {} if params is None else params
        params["page"] = 1

        while True:
            response = self.__http_request(method, endpoint, params=params)
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
            response = self.__http_request(method, endpoint, json_body=json_body)
            result += response.json()

            if "x-next-row-number" in response.headers:
                json_body["first_row_number"] = int(
                    response.headers["x-next-row-number"]
                )
            else:
                break

        return result
