import httpx

from app.models.toggl import Organization, User, TimeEntry, Workspace


class Api:
    def __init__(
        self,
        api_token,
        base_url="https://api.track.toggl.com",
    ):
        self.api_token = api_token
        self.base_url = base_url
        self.client = httpx.Client()

    def get_me(self) -> User:
        req = self.__request("GET", "/api/v9/me")
        data = req.json()
        return self.__create_user_from_api(data)

    def get_my_organizations(self) -> list[Organization]:
        req = self.__request("GET", "/api/v9/me/organizations")
        data = req.json()
        return list(map(self.__create_organization_from_api, data))

    def get_my_workspaces(self) -> list[Workspace]:
        req = self.__request("GET", "/api/v9/me/all_workspaces")
        data = req.json()
        return list(map(self.__create_workspace_from_api, data))

    def get_time_entries(self, since=None):
        params = {}
        if since is not None:
            params["since"] = since

        req = self.__request("GET", "/api/v9/me/time_entries", params)
        data = req.json()
        return list(map(self.__create_time_entry_from_api, data))

    def __request(
        self, method: str, endpoint: str, params: dict[str, str] = None
    ) -> httpx.Request:
        if params is not None:
            params = {}

        req = self.client.request(
            method=method,
            params=params,
            url=f"{self.base_url}{endpoint}",
            auth=(self.api_token, "api_token"),
        )

        return req

    def __create_user_from_api(self, data: map) -> User:
        return User(
            id=data["id"],
            fullname=data["fullname"],
            email=data["email"],
            country_id=data["country_id"],
            timezone=data["timezone"],
            beginning_of_week=data["beginning_of_week"],
            image_url=data["image_url"],
            created_at=data["created_at"],
            updated_at=data["at"],
            api_token=data["api_token"],
        )

    def __create_organization_from_api(self, data: map) -> Organization:
        return Organization(
            id=data["id"],
            name=data["name"],
            created_at=data["created_at"],
            updated_at=data["at"],
            deleted_at=data["server_deleted_at"],
        )

    def __create_workspace_from_api(self, data: map) -> Workspace:
        return Workspace(
            id=data["id"],
            organization_id=data["organization_id"],
            name=data["name"],
            updated_at=data["at"],
            deleted_at=data["server_deleted_at"],
            logo_url=data["logo_url"],
        )

    def __create_time_entry_from_api(self, data: map) -> TimeEntry:
        return TimeEntry(
            id=data["id"],
            description=data["description"],
            start=data["start"],
            stop=data["stop"],
            updated_at=data["at"],
            user_id=data["user_id"],
            workspace_id=data["workspace_id"],
        )
